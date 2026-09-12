"""Timeline engine para proyectos M1–M3 (Phase 7.2)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from aicos.application.cinematic_timeline.presentation import snapshot_to_out
from aicos.database.db import ProjectRow, session_scope
from aicos.models.schemas import (
    ProjectTimelineMergeRequest,
    ProjectTimelineReorderRequest,
    ProjectTimelineReplaceClipRequest,
    ProjectTimelineSnapshotOut,
    ProjectTimelineSplitRequest,
    ProjectTimelineTrimRequest,
)
from aicos.services.cinematic_timeline_factory import build_project_timeline_service

router = APIRouter()


def _require_project(session, project_id: str) -> None:
    if session.get(ProjectRow, project_id) is None:
        raise HTTPException(status_code=404, detail="project_not_found")


@router.get("/{project_id}/timeline", response_model=ProjectTimelineSnapshotOut)
def get_project_timeline(project_id: str) -> ProjectTimelineSnapshotOut:
    svc = build_project_timeline_service()
    with session_scope() as session:
        _require_project(session, project_id)
        result = svc.get_snapshot(session, project_id)
    return snapshot_to_out(result.scenes, project_id=project_id, timeline_duration_ms=result.timeline_duration_ms)


@router.post("/{project_id}/timeline/reorder", response_model=ProjectTimelineSnapshotOut)
def reorder_timeline(project_id: str, body: ProjectTimelineReorderRequest) -> ProjectTimelineSnapshotOut:
    svc = build_project_timeline_service()
    try:
        with session_scope() as session:
            _require_project(session, project_id)
            result = svc.reorder(session, project_id, from_index=body.from_index, to_index=body.to_index)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return snapshot_to_out(result.scenes, project_id=project_id, timeline_duration_ms=result.timeline_duration_ms)


@router.post("/{project_id}/timeline/merge", response_model=ProjectTimelineSnapshotOut)
def merge_timeline_scenes(project_id: str, body: ProjectTimelineMergeRequest) -> ProjectTimelineSnapshotOut:
    svc = build_project_timeline_service()
    try:
        with session_scope() as session:
            _require_project(session, project_id)
            result = svc.merge(
                session,
                project_id,
                scene_index_a=body.scene_index_a,
                scene_index_b=body.scene_index_b,
            )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return snapshot_to_out(result.scenes, project_id=project_id, timeline_duration_ms=result.timeline_duration_ms)


@router.post("/{project_id}/timeline/split", response_model=ProjectTimelineSnapshotOut)
def split_timeline_scene(project_id: str, body: ProjectTimelineSplitRequest) -> ProjectTimelineSnapshotOut:
    svc = build_project_timeline_service()
    try:
        with session_scope() as session:
            _require_project(session, project_id)
            result = svc.split(session, project_id, scene_id=body.scene_id, split_at_ms=body.split_at_ms)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return snapshot_to_out(result.scenes, project_id=project_id, timeline_duration_ms=result.timeline_duration_ms)


@router.post("/{project_id}/timeline/trim", response_model=ProjectTimelineSnapshotOut)
def trim_timeline_scene(project_id: str, body: ProjectTimelineTrimRequest) -> ProjectTimelineSnapshotOut:
    svc = build_project_timeline_service()
    try:
        with session_scope() as session:
            _require_project(session, project_id)
            result = svc.trim(
                session,
                project_id,
                scene_id=body.scene_id,
                start_ms=body.start_ms,
                end_ms=body.end_ms,
            )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return snapshot_to_out(result.scenes, project_id=project_id, timeline_duration_ms=result.timeline_duration_ms)


@router.post("/{project_id}/timeline/replace-clip", response_model=ProjectTimelineSnapshotOut)
def replace_timeline_clip(project_id: str, body: ProjectTimelineReplaceClipRequest) -> ProjectTimelineSnapshotOut:
    svc = build_project_timeline_service()
    try:
        with session_scope() as session:
            _require_project(session, project_id)
            result = svc.replace_clip(
                session,
                project_id,
                scene_id=body.scene_id,
                clip_id=body.clip_id,
            )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return snapshot_to_out(result.scenes, project_id=project_id, timeline_duration_ms=result.timeline_duration_ms)
