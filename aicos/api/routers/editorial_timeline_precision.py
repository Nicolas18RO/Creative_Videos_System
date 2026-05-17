"""Rutas REST Fase 6.8 — edición precisa de timeline (orquestación fina)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from aicos.application.editorial_dataset.ports import RawTimelineSceneInput
from aicos.application.editorial_dataset.creative_dataset_export_service import timeline_to_dataset_record
from aicos.application.editorial_training.timeline_precision_presentation import (
    adjustment_to_out,
    merge_preview_to_out,
    validation_to_out,
)
from aicos.database.db import session_scope
from aicos.domain.editorial_training.timeline_rules import SceneBoundary
from aicos.models.schemas import (
    MergePreviewRequest,
    MergePreviewResultOut,
    TimelineSaveAdjustmentsRequest,
    TimelineSaveAdjustmentsResponse,
    TimelineValidateRequest,
    TimelineValidationResultOut,
)
from aicos.services.editorial_timeline_precision_factory import build_timeline_precision_service

router = APIRouter()


def _raw_from_submit(body: TimelineSaveAdjustmentsRequest) -> tuple[RawTimelineSceneInput, ...]:
    return tuple(
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


@router.post("/validate", response_model=TimelineValidationResultOut)
def validate_timeline(body: TimelineValidateRequest) -> TimelineValidationResultOut:
    svc = build_timeline_precision_service()
    boundaries = tuple(
        SceneBoundary(scene_index=s.scene_index, start_time=s.start_time, end_time=s.end_time)
        for s in body.scenes
    )
    result = svc.validate_timeline_draft(
        boundaries,
        timeline_duration=body.timeline_duration,
        session_id=body.session_id,
    )
    return validation_to_out(result)


@router.post("/merge-preview", response_model=MergePreviewResultOut)
def merge_preview(body: MergePreviewRequest) -> MergePreviewResultOut:
    svc = build_timeline_precision_service()
    try:
        with session_scope() as session:
            preview = svc.merge_preview(
                session,
                body.creative_id,
                body.scene_index_a,
                body.scene_index_b,
            )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return merge_preview_to_out(preview)


@router.post("/sessions/{session_id}/save-adjustments", response_model=TimelineSaveAdjustmentsResponse)
def save_timeline_adjustments(session_id: str, body: TimelineSaveAdjustmentsRequest) -> TimelineSaveAdjustmentsResponse:
    if body.session_id != session_id:
        raise HTTPException(status_code=400, detail="session_id_mismatch")
    svc = build_timeline_precision_service()
    raw = _raw_from_submit(body)
    try:
        with session_scope() as session:
            timeline, validation, saved = svc.save_timeline_adjustments(
                session,
                session_id,
                raw,
                adjustment_reason=body.adjustment_reason,
                timeline_duration=body.timeline_duration,
            )
    except ValueError as e:
        detail = str(e)
        status = 400
        if detail == "timeline_validation_failed":
            status = 422
        raise HTTPException(status_code=status, detail=detail) from e
    return TimelineSaveAdjustmentsResponse(
        validation=validation_to_out(validation),
        adjustments_saved=[adjustment_to_out(a) for a in saved],
        timeline=timeline_to_dataset_record(timeline),
    )
