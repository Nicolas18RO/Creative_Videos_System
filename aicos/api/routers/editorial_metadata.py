"""Rutas REST editorial (Fase 5.3): delegación a servicios de aplicación."""

from __future__ import annotations

import logging
from dataclasses import asdict

from fastapi import APIRouter, HTTPException, Query

from aicos.config import get_config
from aicos.database.db import session_scope
from aicos.domain.editorial_metadata.entities import EditorialFeedbackSignal
from aicos.models.schemas import (
    EditorialBulkUpdateRequest,
    EditorialBulkUpdateResponse,
    EditorialClusterListResponse,
    EditorialFeedbackCreate,
    EditorialFeedbackResponse,
    EditorialMetadataSchema,
    EditorialPatchRequest,
)
from aicos.services.editorial_metadata_factory import (
    build_editorial_feedback_service,
    build_editorial_metadata_service,
)

logger = logging.getLogger(__name__)
router = APIRouter()


def _require_editorial() -> None:
    cfg = get_config().editorial_metadata
    if not cfg.enabled:
        raise HTTPException(status_code=404, detail="editorial_metadata_disabled")


def _to_schema(record) -> EditorialMetadataSchema:
    return EditorialMetadataSchema(**asdict(record))


@router.get("/clips/{clip_id}", response_model=EditorialMetadataSchema)
def get_clip_editorial(clip_id: str) -> EditorialMetadataSchema:
    _require_editorial()
    with session_scope() as session:
        svc = build_editorial_metadata_service()
        rec = svc.get_clip(session, clip_id)
        if rec is None:
            raise HTTPException(status_code=404, detail="clip_not_found")
        return _to_schema(rec)


@router.patch("/clips/{clip_id}", response_model=EditorialMetadataSchema)
def patch_clip_editorial(
    clip_id: str,
    body: EditorialPatchRequest,
    corrected_by: str = Query("editor", description="Identificador humano o servicio"),
    correction_reason: str = Query("manual_patch", description="Motivo de la corrección"),
) -> EditorialMetadataSchema:
    _require_editorial()
    patch = body.model_dump(exclude_unset=True)
    if not patch:
        raise HTTPException(status_code=400, detail="empty_patch")
    with session_scope() as session:
        svc = build_editorial_metadata_service()
        try:
            rec = svc.patch_clip(
                session,
                clip_id=clip_id,
                fields=patch,
                corrected_by=corrected_by,
                correction_reason=correction_reason,
            )
        except LookupError:
            raise HTTPException(status_code=404, detail="clip_not_found") from None
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e)) from e
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
        return _to_schema(rec)


@router.post("/feedback", response_model=EditorialFeedbackResponse)
def post_editorial_feedback(body: EditorialFeedbackCreate) -> EditorialFeedbackResponse:
    _require_editorial()
    sig = EditorialFeedbackSignal(
        clip_id=body.clip_id,
        usefulness_score=body.usefulness_score,
        continuity_score=body.continuity_score,
        diversity_score=body.diversity_score,
        narrative_quality=body.narrative_quality,
        visual_quality=body.visual_quality,
        human_feedback=body.human_feedback,
    )
    with session_scope() as session:
        fb = build_editorial_feedback_service()
        fid = fb.submit(session, sig)
    return EditorialFeedbackResponse(feedback_id=fid or "ephemeral", clip_id=body.clip_id)


@router.get("/clusters/{cluster_id}", response_model=EditorialClusterListResponse)
def list_cluster_clips(
    cluster_id: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> EditorialClusterListResponse:
    _require_editorial()
    with session_scope() as session:
        svc = build_editorial_metadata_service()
        try:
            clips = svc.list_cluster(session, cluster_id=cluster_id, limit=limit, offset=offset)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
        return EditorialClusterListResponse(
            cluster_id=cluster_id,
            limit=limit,
            offset=offset,
            clips=[_to_schema(c) for c in clips],
        )


@router.post("/bulk-update", response_model=EditorialBulkUpdateResponse)
def bulk_update_editorial(body: EditorialBulkUpdateRequest) -> EditorialBulkUpdateResponse:
    _require_editorial()
    cfg = get_config().editorial_metadata
    if not cfg.enable_bulk_operations:
        raise HTTPException(status_code=403, detail="bulk_operations_disabled")
    if len(body.items) > 500:
        raise HTTPException(status_code=400, detail="too_many_items_max_500")
    tuples: list[tuple[str, dict]] = []
    for it in body.items:
        p = it.patch.model_dump(exclude_unset=True)
        if p:
            tuples.append((it.clip_id, p))
    if not tuples:
        raise HTTPException(status_code=400, detail="empty_bulk")
    with session_scope() as session:
        svc = build_editorial_metadata_service()
        try:
            n = svc.bulk_patch(
                session,
                items=tuples,
                corrected_by=body.corrected_by,
                correction_reason=body.correction_reason,
            )
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e)) from e
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
    return EditorialBulkUpdateResponse(updated=n)
