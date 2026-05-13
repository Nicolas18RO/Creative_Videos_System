"""Orquestación de búsqueda semántica con memoria de uso (API → servicios → módulos)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

from aicos.application.cinematic.contextual_retrieval_service import get_contextual_retrieval_service
from aicos.config import get_config
from aicos.models.schemas import Recommendation, SearchRequest, SearchResponse, SearchRunContext
from aicos.services.prompt_intelligence_service import (
    compute_audio_session_penalties,
    compute_intelligence_boosts,
    query_fingerprint,
    record_audio_segment_search,
    record_search_pool,
)

if TYPE_CHECKING:
    from aicos.core.embedder import Embedder
    from aicos.core.vector_store import VectorStore

logger = logging.getLogger(__name__)


def _safe_get_app_config():
    """Config con fallback para pipelines (evita propagar fallos de YAML)."""
    try:
        return get_config()
    except Exception as e:
        logger.warning("[SearchPipeline] get_config_failed: %s", e)
        return None


def run_search(
    session: Session,
    req: SearchRequest,
    embedder: Embedder,
    store: VectorStore,
    context: SearchRunContext | None = None,
) -> SearchResponse:
    """Búsqueda con boosts taxonómicos + inteligencia por historial; contexto opcional (p. ej. audio)."""
    app_cfg = _safe_get_app_config()
    search_cfg = app_cfg.search if app_cfg is not None else None
    if search_cfg is None:
        from aicos.config import SearchConfig

        search_cfg = SearchConfig()
        logger.warning("[SearchPipeline] using_default_search_config=true")
    gap_threshold = search_cfg.gap_threshold
    fp = query_fingerprint(req)

    from aicos.modules.clip_recommender import build_ranked_recommendations

    recs = build_ranked_recommendations(req, embedder, store)
    mr = None
    if app_cfg is not None:
        mr = getattr(app_cfg, "multimodal_retrieval", None)
    if mr is not None and mr.enabled and mr.enable_visual_similarity and recs:
        try:
            from aicos.modules.multimodal_hybrid_retrieval import apply_multimodal_hybrid_to_recommendations

            recs = apply_multimodal_hybrid_to_recommendations(
                recs, req, retrieval_cfg=mr, context=context
            )
        except Exception as e:
            logger.warning("[MultimodalRetrieval] hybrid_skip error=%s", e)
    em = None
    if app_cfg is not None:
        em = getattr(app_cfg, "editorial_metadata", None)
    if em is not None and em.enabled and em.enable_editorial_boosts and recs:
        try:
            from aicos.services.editorial_ranking_integration import (
                apply_editorial_boosts_to_recommendations,
            )

            recs = apply_editorial_boosts_to_recommendations(
                session, recs, req, editorial_cfg=em
            )
        except Exception as e:
            logger.warning("[EditorialMetadata] ranking_boost_skip error=%s", e)
    if not recs:
        logger.info("[SearchPipeline] empty_candidates query_fp=%s apply_intelligence=%s", fp, req.apply_intelligence)
        return SearchResponse(results=[], is_gap=True, query_fingerprint=fp)

    cr_on = False
    if app_cfg is not None:
        cr = getattr(app_cfg, "contextual_retrieval", None)
        cr_on = bool(cr and getattr(cr, "enabled", False))
    if context is not None and context.ranking_context is not None and cr_on:
        try:
            crs = get_contextual_retrieval_service()
            recs = crs.apply_pipeline(recs, req, context.ranking_context, embedder=embedder)
            rk = context.ranking_context
            logger.info(
                "[ContextualRetrieval] scene_index=%s candidate_pool=%d top_clip=%s "
                "global_domain=%s anchors=%s",
                getattr(context, "scene_index", None),
                len(recs),
                recs[0].clip_id if recs else "none",
                (rk.industry or "")[:48] if rk else "",
                list((rk.semantic_anchors or [])[:8]) if rk else [],
            )
        except Exception as e:
            logger.warning("[ContextualRetrieval] rerank_skip error=%s", e)
    is_audio = context is not None and context.source == "audio"
    nm_on = False
    if app_cfg is not None:
        nm = getattr(app_cfg, "narrative_memory", None)
        nm_on = bool(nm and getattr(nm, "enabled", False))
    if (
        is_audio
        and context is not None
        and context.correlation_id
        and nm_on
        and recs
    ):
        try:
            from aicos.application.cinematic.narrative_memory_service import get_narrative_memory_service

            nms = get_narrative_memory_service()
            recs = nms.apply_for_search(session, recs, req, context)
        except Exception as e:
            logger.warning("[NarrativeMemory] apply_skip error=%s", e)
    cui_on = False
    if app_cfg is not None:
        cu = getattr(app_cfg, "clip_usage_intelligence", None)
        cui_on = bool(cu and getattr(cu, "enabled", False))
    if is_audio and context is not None and context.correlation_id and cui_on and recs:
        try:
            from aicos.application.clip_usage.clip_usage_intelligence_service import (
                get_clip_usage_intelligence_service,
            )

            recs = get_clip_usage_intelligence_service().apply_for_search(recs, req, context, session)
        except Exception as e:
            logger.warning("[ClipUsage] apply_skip error=%s", e)
    pool_ids = [r.clip_id for r in recs[:40]]

    if req.record_usage and pool_ids:
        try:
            if is_audio and context is not None:
                record_audio_segment_search(session, req=req, context=context, candidate_ids=pool_ids)
            elif not is_audio:
                record_search_pool(session, req=req, candidate_ids=pool_ids)
        except Exception as e:
            logger.warning("No se pudo registrar evento de búsqueda: %s", e)

    boosts: dict[str, float] = {}
    if req.apply_intelligence:
        boosts = compute_intelligence_boosts(
            session,
            clip_ids=[r.clip_id for r in recs],
            query_fp=fp,
            narrative_function=req.narrative_function,
        )
    if is_audio and req.apply_intelligence:
        for cid, pen in compute_audio_session_penalties(
            clip_ids=[r.clip_id for r in recs], used_clip_ids=req.used_clip_ids
        ).items():
            boosts[cid] = boosts.get(cid, 0.0) + pen

    adjusted: list[Recommendation] = []
    for r in recs:
        ib = float(boosts.get(r.clip_id, 0.0))
        # ``final_score`` puede incluir reranking contextual (híbrido + taxonomía); no re-sumar taxonomía.
        fs = max(0.0, min(1.0, float(r.final_score) + ib))
        adjusted.append(
            r.model_copy(
                update={
                    "intelligence_boost": ib,
                    "final_score": fs,
                }
            )
        )
    adjusted.sort(key=lambda r: (-r.final_score, r.clip_id))
    top: list[Recommendation] = []
    for i, r in enumerate(adjusted[: req.n_results], start=1):
        top.append(r.model_copy(update={"rank": i}))
    is_gap = not top or top[0].final_score < gap_threshold
    if is_audio and context is not None and top:
        gdom = ""
        if context.ranking_context and context.ranking_context.industry:
            gdom = (context.ranking_context.industry or "")[:64]
        elif context.global_context and context.global_context.industry:
            gdom = (context.global_context.industry or "")[:64]
        logger.info(
            "[FinalSelection] scene_index=%s correlation_id=%s selected_clip=%s final_score=%.4f "
            "intelligence_boost=%.4f is_gap=%s global_domain=%s",
            getattr(context, "scene_index", None),
            context.correlation_id or "",
            top[0].clip_id,
            float(top[0].final_score),
            float(top[0].intelligence_boost),
            is_gap,
            gdom,
        )
    if (
        is_audio
        and context is not None
        and context.correlation_id is not None
        and context.scene_index is not None
        and top
        and app_cfg is not None
    ):
        cui_cfg = getattr(app_cfg, "clip_usage_intelligence", None)
        if cui_cfg and getattr(cui_cfg, "persist_history", False):
            try:
                from aicos.application.cinematic_metadata.resolver import CinematicMetadataResolver
                from aicos.services import clip_usage_repository
                from aicos.services.cinematic_metadata_read_factory import create_cinematic_metadata_read_port

                c0 = top[0]
                store = create_cinematic_metadata_read_port(session)
                resolver = CinematicMetadataResolver(store)
                clip_usage_repository.append_clip_usage_history(
                    session,
                    correlation_id=context.correlation_id,
                    scene_index=context.scene_index,
                    clip_id=c0.clip_id,
                    source_video_id=resolver.resolve_source_video_id(c0),
                    visual_cluster_id=resolver.resolve_visual_cluster_id(c0),
                    final_score=float(c0.final_score),
                    penalties_json=None,
                )
            except Exception as e:
                logger.warning("[ClipUsage] history_persist_skip: %s", e)
    return SearchResponse(results=top, is_gap=is_gap, query_fingerprint=fp)
