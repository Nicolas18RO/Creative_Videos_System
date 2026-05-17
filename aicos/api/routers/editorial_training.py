"""Rutas REST Fase 6.7 — workspace de entrenamiento editorial (solo orquestación)."""

from __future__ import annotations

import re
import uuid
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from aicos.application.editorial_dataset.creative_dataset_export_service import timeline_to_dataset_record
from aicos.application.editorial_dataset.ports import RawTimelineSceneInput
from aicos.application.editorial_training.editorial_training_views import build_timeline_scene_cards, build_training_summary
from aicos.config import get_config
from aicos.database.db import session_scope
from aicos.domain.editorial_training.entities import EditorialTrainingCorrectionItem, EditorialTrainingSession
from aicos.models.schemas import (
    EditorialTrainingAnalyzeRequest,
    EditorialTrainingAnalyzeResponse,
    EditorialTrainingCorrectionsRequest,
    EditorialTrainingSessionCreateRequest,
    EditorialTrainingSessionOut,
    EditorialTrainingTimelineSubmitRequest,
    EditorialTrainingWorkspaceGetResponse,
    UploadEditorialAssetResponse,
)
from aicos.services.editorial_training_factory import (
    build_editorial_training_analyze_service,
    build_editorial_training_upload_service,
    build_editorial_training_workspace_service,
)

router = APIRouter()


def _require_workspace() -> None:
    cfg = get_config()
    if not cfg.editorial_training_workspace.enabled:
        raise HTTPException(status_code=404, detail="editorial_training_workspace_disabled")


def _require_editorial_dataset() -> None:
    if not get_config().editorial_dataset.enabled:
        raise HTTPException(status_code=404, detail="editorial_dataset_disabled")


def _derive_creative_id(body: EditorialTrainingSessionCreateRequest) -> str:
    cid = (body.creative_id or "").strip()
    if cid:
        return cid[:128]
    base = re.sub(r"\W+", "_", (body.creative_name or "creative").strip().lower()).strip("_")[:60] or "creative"
    return f"{base}_{uuid.uuid4().hex[:10]}"


def _session_out(s: EditorialTrainingSession) -> EditorialTrainingSessionOut:
    return EditorialTrainingSessionOut(
        session_id=s.session_id,
        creative_id=s.creative_id,
        project_id=s.project_id,
        status=s.status,
        final_video_path=s.final_video_path,
        audio_path=s.audio_path,
        corrections_count=len(s.corrections),
        created_at=s.created_at.isoformat(),
        updated_at=s.updated_at.isoformat(),
        project_label=s.project_label,
        creative_label=s.creative_label,
        product_category=s.product_category,
        notes=s.notes,
    )


def _scene_cards_for_session(session: Any, timeline: Any, session_id: str):
    previews = None
    reviews = None
    cfg = get_config()
    if cfg.timeline_visualization.enabled:
        try:
            from aicos.services.timeline_visualization_factory import build_timeline_visualization_service

            viz = build_timeline_visualization_service(cfg)
            track = viz.build_visual_track(session, timeline.creative_id)
            previews = track.clip_previews
        except Exception:
            previews = None
    try:
        from aicos.infrastructure.editorial_review.sql_editorial_scene_review_repository import (
            SqlEditorialSceneReviewRepository,
        )

        reviews = SqlEditorialSceneReviewRepository().list_by_session(session, session_id)
    except Exception:
        reviews = None
    return build_timeline_scene_cards(
        timeline,
        visual_previews=previews,
        creative_id=timeline.creative_id,
        review_states=reviews,
    )


def _analyze_response_payload(
    s: EditorialTrainingSession, timeline: Any, analysis_warning: str | None, session: Any
) -> EditorialTrainingAnalyzeResponse:
    rec = timeline_to_dataset_record(timeline)
    cards = _scene_cards_for_session(session, timeline, s.session_id)
    summary = build_training_summary(s, timeline)
    return EditorialTrainingAnalyzeResponse(
        session=_session_out(s),
        timeline=rec,
        scene_cards=cards,
        summary=summary,
        analysis_warning=analysis_warning,
    )


@router.post("/sessions", response_model=EditorialTrainingSessionOut)
def create_training_session(body: EditorialTrainingSessionCreateRequest) -> EditorialTrainingSessionOut:
    _require_workspace()
    svc = build_editorial_training_workspace_service()
    try:
        with session_scope() as session:
            s = svc.create_session(
                session,
                creative_id=_derive_creative_id(body),
                project_id=body.project_id,
                final_video_path=body.final_video_path,
                audio_path=body.audio_path,
                project_label=body.project_name,
                creative_label=body.creative_name,
                product_category=body.product_category,
                notes=body.notes,
            )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return _session_out(s)


@router.get("/sessions/{session_id}", response_model=EditorialTrainingWorkspaceGetResponse)
def get_training_session(session_id: str) -> EditorialTrainingWorkspaceGetResponse:
    _require_workspace()
    svc = build_editorial_training_workspace_service()
    with session_scope() as session:
        s = svc.get_session(session, session_id)
        if s is None:
            raise HTTPException(status_code=404, detail="editorial_training_session_not_found")
        tl = svc.load_timeline(session, s.creative_id)
        timeline_dict = timeline_to_dataset_record(tl) if tl is not None else None
        cards = _scene_cards_for_session(session, tl, session_id) if tl is not None else []
        summary = build_training_summary(s, tl) if tl is not None else None
        review_summary = None
        if tl is not None:
            try:
                from aicos.application.editorial_review.workspace_integration import load_review_summary_for_session
                from aicos.infrastructure.editorial_review.sql_editorial_scene_review_repository import (
                    SqlEditorialSceneReviewRepository,
                )
                from aicos.services.editorial_review_factory import build_timeline_review_service

                review_summary = load_review_summary_for_session(
                    session,
                    session_id,
                    s.creative_id,
                    timeline_read=SqlCreativeTimelineRepository(),
                    review_svc=build_timeline_review_service(),
                    review_repo=SqlEditorialSceneReviewRepository(),
                )
            except Exception:
                review_summary = None
    return EditorialTrainingWorkspaceGetResponse(
        session=_session_out(s),
        timeline=timeline_dict,
        scene_cards=cards,
        summary=summary,
        review_summary=review_summary,
    )


@router.post("/upload/video", response_model=UploadEditorialAssetResponse)
async def upload_training_video(
    session_id: str = Form(...),
    file: UploadFile = File(...),
) -> UploadEditorialAssetResponse:
    _require_workspace()
    upload_svc = build_editorial_training_upload_service()
    workspace = build_editorial_training_workspace_service()
    data = await file.read()
    try:
        stored = upload_svc.save_video(session_id, file.filename or "video.mp4", data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    try:
        with session_scope() as session:
            workspace.update_media_paths(session, session_id, final_video_path=stored.absolute_path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return UploadEditorialAssetResponse(
        session_id=session_id,
        path=stored.absolute_path,
        stored_filename=stored.stored_filename,
        size_bytes=stored.size_bytes,
        duration_ms=stored.duration_ms,
    )


@router.post("/upload/audio", response_model=UploadEditorialAssetResponse)
async def upload_training_audio(
    session_id: str = Form(...),
    file: UploadFile = File(...),
) -> UploadEditorialAssetResponse:
    _require_workspace()
    upload_svc = build_editorial_training_upload_service()
    workspace = build_editorial_training_workspace_service()
    data = await file.read()
    try:
        stored = upload_svc.save_audio(session_id, file.filename or "audio.wav", data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    try:
        with session_scope() as session:
            workspace.update_media_paths(session, session_id, audio_path=stored.absolute_path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return UploadEditorialAssetResponse(
        session_id=session_id,
        path=stored.absolute_path,
        stored_filename=stored.stored_filename,
        size_bytes=stored.size_bytes,
        duration_ms=stored.duration_ms,
    )


@router.post("/analyze", response_model=EditorialTrainingAnalyzeResponse)
async def analyze_training_session(body: EditorialTrainingAnalyzeRequest) -> EditorialTrainingAnalyzeResponse:
    _require_workspace()
    _require_editorial_dataset()
    analyze_svc = build_editorial_training_analyze_service()
    workspace = build_editorial_training_workspace_service()
    try:
        with session_scope() as session:
            timeline, resp = await analyze_svc.run(session, body.session_id)
            s = workspace.get_session(session, body.session_id)
            if s is None:
                raise HTTPException(status_code=404, detail="editorial_training_session_not_found")
            return _analyze_response_payload(s, timeline, resp.warning, session)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/sessions/{session_id}/timeline", response_model=dict)
def submit_training_timeline(session_id: str, body: EditorialTrainingTimelineSubmitRequest) -> dict:
    _require_workspace()
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
    svc = build_editorial_training_workspace_service()
    try:
        with session_scope() as session:
            timeline = svc.submit_timeline(session, session_id, raw)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return timeline_to_dataset_record(timeline)


@router.post("/sessions/{session_id}/corrections", response_model=EditorialTrainingSessionOut)
def post_training_corrections(session_id: str, body: EditorialTrainingCorrectionsRequest) -> EditorialTrainingSessionOut:
    _require_workspace()
    items = tuple(
        EditorialTrainingCorrectionItem(
            event_kind=i.event_kind,
            reward=i.reward,
            clip_id=i.clip_id,
            replaced_clip_id=i.replaced_clip_id,
            scene_index=i.scene_index,
            narrative_function=i.narrative_function,
            transition_type=i.transition_type,
        )
        for i in body.items
    )
    svc = build_editorial_training_workspace_service()
    try:
        with session_scope() as session:
            s = svc.apply_corrections(session, session_id, items)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return _session_out(s)


@router.post("/sessions/{session_id}/commit", response_model=EditorialTrainingSessionOut)
def commit_training_session(session_id: str) -> EditorialTrainingSessionOut:
    _require_workspace()
    _require_editorial_dataset()
    svc = build_editorial_training_workspace_service()
    try:
        with session_scope() as session:
            s = svc.commit_learning(session, session_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return _session_out(s)
