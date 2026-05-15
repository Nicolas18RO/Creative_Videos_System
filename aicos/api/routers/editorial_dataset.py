"""Rutas REST Fase 6.1 — delegación a servicios de aplicación (sin lógica editorial)."""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException

from aicos.application.editorial_dataset.creative_dataset_export_service import timeline_to_dataset_record
from aicos.application.editorial_dataset.ports import RawTimelineSceneInput
from aicos.config import get_config
from aicos.database.db import session_scope
from aicos.domain.editorial_recommendation.entities import EditorialRecommendationPlan
from aicos.models.schemas import (
    ClipSearchContextHintOut,
    EditorialDatasetBuildFromJsonRequest,
    EditorialDatasetBuildRequest,
    EditorialDatasetExportJsonlRequest,
    EditorialRecommendationItemOut,
    EditorialRecommendationPlanResponse,
    StyleMemoryPeerOut,
    StyleRetrievalSimilarHitOut,
    StyleRetrievalSimilarResponse,
)
from aicos.services.editorial_dataset_factory import (
    build_creative_dataset_export_service,
    build_creative_timeline_builder_service,
)

logger = logging.getLogger(__name__)
router = APIRouter()


def _require_editorial_dataset() -> None:
    if not get_config().editorial_dataset.enabled:
        raise HTTPException(status_code=404, detail="editorial_dataset_disabled")


@router.post("/timelines/build")
def build_timeline_inline(body: EditorialDatasetBuildRequest) -> dict:
    _require_editorial_dataset()
    raw = tuple(
        RawTimelineSceneInput(
            scene_index=s.scene_index,
            clip_id=s.clip_id,
            start_time=s.start_time,
            end_time=s.end_time,
            transition_type=s.transition_type,
            narrative_role=s.narrative_role,
            motion_intensity=s.motion_intensity,
            visual_energy=s.visual_energy,
            camera_type=s.camera_type,
            semantic_tags=tuple(s.semantic_tags),
            emotion_tags=tuple(s.emotion_tags),
        )
        for s in sorted(body.scenes, key=lambda x: x.scene_index)
    )
    with session_scope() as session:
        builder = build_creative_timeline_builder_service(with_persistence=True)
        timeline = builder.build_from_raw_scenes(
            creative_id=body.creative_id,
            audio_path=body.audio_path,
            final_video_path=body.final_video_path,
            raw_scenes=raw,
            session=session,
        )
    return timeline_to_dataset_record(timeline)


@router.post("/timelines/build-from-json")
def build_timeline_from_json(body: EditorialDatasetBuildFromJsonRequest) -> dict:
    _require_editorial_dataset()
    path = Path(body.timeline_json_path).expanduser()
    with session_scope() as session:
        builder = build_creative_timeline_builder_service(with_persistence=True)
        timeline = builder.build_from_json_path(path, session=session)
    return timeline_to_dataset_record(timeline)


@router.get("/timelines/{creative_id}")
def get_timeline(creative_id: str) -> dict:
    _require_editorial_dataset()
    from aicos.infrastructure.editorial_dataset.sqlite_creative_timeline_repository import (
        SqlCreativeTimelineRepository,
    )

    repo = SqlCreativeTimelineRepository()
    with session_scope() as session:
        t = repo.get_by_creative_id(session, creative_id)
    if t is None:
        raise HTTPException(status_code=404, detail="creative_timeline_not_found")
    return timeline_to_dataset_record(t)


@router.post("/export/jsonl")
def export_jsonl_dataset(body: EditorialDatasetExportJsonlRequest) -> dict:
    _require_editorial_dataset()
    cfg = get_config()
    if not cfg.editorial_dataset.export_jsonl:
        raise HTTPException(status_code=400, detail="export_jsonl_disabled")
    from aicos.infrastructure.editorial_dataset.sqlite_creative_timeline_repository import (
        SqlCreativeTimelineRepository,
    )

    repo = SqlCreativeTimelineRepository()
    timelines = []
    with session_scope() as session:
        for cid in body.creative_ids:
            t = repo.get_by_creative_id(session, cid)
            if t is not None:
                timelines.append(t)
    if not timelines:
        raise HTTPException(status_code=404, detail="no_timelines_found")
    out_dir = cfg.resolved_paths()["exports"]
    out_path = out_dir / body.output_filename
    exporter = build_creative_dataset_export_service()
    exporter.export_jsonl(tuple(timelines), out_path)
    logger.info("[EditorialDataset] export_jsonl_written path=%s", out_path)
    return {"path": str(out_path), "rows": len(timelines)}


@router.get("/style-embeddings/{creative_id}")
def get_style_embedding(creative_id: str) -> dict:
    _require_editorial_dataset()
    if not get_config().editorial_style_embedding.enabled:
        raise HTTPException(status_code=404, detail="editorial_style_embedding_disabled")
    from aicos.infrastructure.editorial_style_embedding.sql_editorial_style_embedding_repository import (
        SqlEditorialStyleEmbeddingRepository,
    )

    with session_scope() as session:
        emb = SqlEditorialStyleEmbeddingRepository().get_by_creative_id(session, creative_id)
    if emb is None:
        raise HTTPException(status_code=404, detail="style_embedding_not_found")
    return {
        "creative_id": emb.creative_id,
        "digest_sha256": emb.digest_sha256,
        "structural_dim": len(emb.structural_vector),
        "semantic_dim": len(emb.semantic_vector) if emb.semantic_vector else 0,
        "fused_dim": len(emb.fused_vector),
        "fusion_mode": emb.fusion_mode,
        "structural_model": emb.structural_model_tag,
        "semantic_model": emb.semantic_model_tag,
    }


@router.get("/style-retrieval/similar", response_model=StyleRetrievalSimilarResponse)
def style_retrieval_similar(
    creative_id: str,
    top_k: int | None = None,
    exclude_self: bool = True,
) -> StyleRetrievalSimilarResponse:
    _require_editorial_dataset()
    cfg = get_config()
    if not cfg.editorial_style_retrieval.enabled:
        raise HTTPException(status_code=404, detail="editorial_style_retrieval_disabled")
    if not cfg.editorial_style_embedding.enabled:
        raise HTTPException(status_code=400, detail="editorial_style_embedding_required_for_retrieval")

    from aicos.services.editorial_style_retrieval_factory import build_editorial_style_retrieval_service

    svc = build_editorial_style_retrieval_service(cfg)
    with session_scope() as session:
        res = svc.retrieve_similar(
            session,
            anchor_creative_id=creative_id,
            top_k=top_k,
            exclude_self=exclude_self,
        )
    hits = [
        StyleRetrievalSimilarHitOut(
            creative_id=h.creative_id,
            rank=h.rank,
            structural_similarity=h.structural_similarity,
            semantic_similarity=h.semantic_similarity,
            hybrid_score=h.hybrid_score,
            peer_digest_sha256=h.peer_digest_sha256,
        )
        for h in res.hits
    ]
    return StyleRetrievalSimilarResponse(
        anchor_creative_id=res.anchor_creative_id,
        hits=hits,
        chroma_pool_size=res.chroma_pool_size,
        used_semantic_hybrid=res.used_semantic_hybrid,
    )


def _plan_to_response(plan: EditorialRecommendationPlan) -> EditorialRecommendationPlanResponse:
    items = [
        EditorialRecommendationItemOut(
            recommendation_id=i.recommendation_id,
            kind=i.kind,
            summary=i.summary,
            detail=i.detail,
            confidence=i.confidence,
            sources=list(i.sources),
        )
        for i in plan.items
    ]
    hint_out: ClipSearchContextHintOut | None = None
    if plan.clip_search_hint is not None:
        h = plan.clip_search_hint
        hint_out = ClipSearchContextHintOut(
            query_line=h.query_line,
            global_query_enrichment=h.global_query_enrichment,
            narrative_function_hint=h.narrative_function_hint,
            is_hook_context=h.is_hook_context,
            semantic_tags=list(h.semantic_tags),
        )
    peers = [
        StyleMemoryPeerOut(creative_id=p.creative_id, hybrid_score=p.hybrid_score) for p in plan.style_memory_peers
    ]
    return EditorialRecommendationPlanResponse(
        anchor_creative_id=plan.anchor_creative_id,
        items=items,
        clip_search_hint=hint_out,
        style_memory_peers=peers,
    )


@router.get("/editorial-recommendations/plan", response_model=EditorialRecommendationPlanResponse)
def get_editorial_recommendation_plan(creative_id: str) -> EditorialRecommendationPlanResponse:
    _require_editorial_dataset()
    cfg = get_config()
    if not cfg.editorial_recommendation_engine.enabled:
        raise HTTPException(status_code=404, detail="editorial_recommendation_engine_disabled")
    from aicos.services.editorial_recommendation_engine_factory import build_editorial_recommendation_service

    svc = build_editorial_recommendation_service(cfg)
    with session_scope() as session:
        plan = svc.build_plan(session, creative_id=creative_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="creative_timeline_not_found")
    return _plan_to_response(plan)
