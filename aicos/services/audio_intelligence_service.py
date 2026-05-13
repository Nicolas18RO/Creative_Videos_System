"""Puente entre análisis de audio (M1) y recuperación con inteligencia (search_service + memoria)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

from aicos.config import get_config
from aicos.models.schemas import (
    GlobalContextSummary,
    Scene,
    SearchRequest,
    SearchResponse,
    SearchRankingContext,
    SearchRunContext,
)
from aicos.services import search_service

if TYPE_CHECKING:
    from aicos.core.embedder import Embedder
    from aicos.core.vector_store import VectorStore

logger = logging.getLogger(__name__)


def run_analyze_scene_search(
    session: Session,
    *,
    scene: Scene,
    embedder: Embedder,
    store: VectorStore,
    used_clip_ids: list[str],
    correlation_id: str,
    scene_index: int,
    enable_intelligence: bool,
    n_results: int = 5,
    candidate_pool_size: int = 24,
    global_query_enrichment: str | None = None,
    global_context: GlobalContextSummary | None = None,
    prior_scene_concepts: list[str] | None = None,
    clip_usage_records: list | None = None,
) -> SearchResponse:
    """Una búsqueda por escena: con inteligencia vía ``search_service`` o legacy ``recommend``."""
    q = (scene.concept or scene.text or "").strip()
    if len(q) > 500:
        q = q[:500]
    gqe = global_query_enrichment
    if gqe is None and getattr(scene, "global_query_enrichment", None):
        gqe = scene.global_query_enrichment
    req = SearchRequest(
        query=q,
        narrative_function=scene.narrative_function,
        gender_hint=scene.gender_hint,
        is_hook=scene.is_hook,
        used_clip_ids=list(used_clip_ids),
        n_results=n_results,
        candidate_pool_size=candidate_pool_size,
        record_usage=enable_intelligence,
        apply_intelligence=enable_intelligence,
        global_query_enrichment=gqe,
    )
    if not enable_intelligence:
        from aicos.modules import clip_recommender

        return clip_recommender.recommend(req, embedder, store)
    rk: SearchRankingContext | None = None
    if global_context is not None:
        rk = SearchRankingContext(
            industry=global_context.industry,
            topic=global_context.topic,
            dominant_emotion=global_context.dominant_emotion,
            semantic_anchors=list(global_context.semantic_anchors or []),
            narrative_arc=global_context.narrative_arc,
            visual_style=global_context.visual_style,
            content_intent=global_context.content_intent,
            scene_text=scene.text,
            scene_concept=scene.concept,
            narrative_function=scene.narrative_function,
            previous_selected_clip_ids=list(used_clip_ids),
            prior_scene_concepts=list(prior_scene_concepts or []),
        )
        anchors = list(global_context.semantic_anchors or [])[:12]
        logger.info(
            "[GlobalContext] scene_index=%s topic=%s industry=%s dominant_emotion=%s "
            "narrative_arc=%s anchors=%s scene_concept_preview=%s",
            scene_index,
            (global_context.topic or "")[:120],
            (global_context.industry or "")[:64],
            (global_context.dominant_emotion or "")[:32],
            (global_context.narrative_arc or "")[:48],
            anchors,
            ((scene.concept or "")[:80] or "").replace("\n", " "),
        )
    else:
        logger.info(
            "[GlobalContext] scene_index=%s global_context=missing ranking_degraded=true",
            scene_index,
        )
    ctx = SearchRunContext(
        source="audio",
        correlation_id=correlation_id,
        scene_index=scene_index,
        concept=(scene.concept or "")[:400] or None,
        ranking_context=rk,
        global_context=global_context,
        clip_usage_records=list(clip_usage_records or []),
    )
    resp = search_service.run_search(session, req, embedder, store, context=ctx)
    if clip_usage_records is not None and resp.results:
        from aicos.application.clip_usage.record_factory import build_usage_record_schema

        clip_usage_records.append(build_usage_record_schema(scene_index=scene_index, rec=resp.results[0]))
    nm_enabled = False
    try:
        app_cfg = get_config()
        nm_cfg = getattr(app_cfg, "narrative_memory", None)
        nm_enabled = bool(nm_cfg and getattr(nm_cfg, "enabled", False))
    except Exception as e:
        logger.warning("[AudioIntelligence] config_read_failed scene_index=%s: %s", scene_index, e)

    if enable_intelligence and nm_enabled and resp.results:
        try:
            from aicos.application.cinematic.narrative_memory_service import get_narrative_memory_service

            get_narrative_memory_service().persist_after_top_selection(
                session,
                correlation_id=correlation_id,
                scene_index=scene_index,
                top=resp.results[0],
                scene=scene,
                global_ctx=global_context,
                ranking=rk,
            )
        except Exception as e:
            logger.warning("[NarrativeMemory] persist_skip scene_index=%s: %s", scene_index, e)
    return resp
