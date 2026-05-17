"""Rutas REST Fase 6.8 — timeline visual cinematográfico (solo orquestación)."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from aicos.application.timeline_visualization.presentation import (
    full_response,
    inspection_to_out,
    media_url,
)
from aicos.config import get_config
from aicos.database.db import session_scope
from aicos.models.schemas import (
    ClipVisualInspectionOut,
    TimelineVisualizationGenerateRequest,
    TimelineVisualizationRebuildRequest,
    TimelineVisualizationResponse,
)
from aicos.services.timeline_visualization_factory import build_timeline_visualization_service

router = APIRouter()


def _require_enabled() -> None:
    if not get_config().timeline_visualization.enabled:
        raise HTTPException(status_code=404, detail="timeline_visualization_disabled")


def _parse_scene_id(scene_id: str) -> tuple[str, int]:
    raw = (scene_id or "").strip()
    if ":" in raw:
        cid, idx_s = raw.split(":", 1)
        return cid.strip(), int(idx_s)
    if "__" in raw:
        cid, idx_s = raw.rsplit("__", 1)
        return cid.strip(), int(idx_s)
    raise HTTPException(status_code=400, detail="invalid_scene_id_format")


@router.get("/{creative_id}", response_model=TimelineVisualizationResponse)
def get_timeline_visualization(creative_id: str) -> TimelineVisualizationResponse:
    _require_enabled()
    svc = build_timeline_visualization_service()
    try:
        with session_scope() as session:
            track = svc.build_visual_track(session, creative_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return full_response(track)


@router.post("/generate-previews", response_model=TimelineVisualizationResponse)
def generate_timeline_previews(body: TimelineVisualizationGenerateRequest) -> TimelineVisualizationResponse:
    _require_enabled()
    svc = build_timeline_visualization_service()
    try:
        with session_scope() as session:
            svc.generate_previews(session, body.creative_id, force=body.force)
            track = svc.build_visual_track(session, body.creative_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return full_response(track)


@router.post("/rebuild", response_model=TimelineVisualizationResponse)
def rebuild_timeline_visualization(body: TimelineVisualizationRebuildRequest) -> TimelineVisualizationResponse:
    _require_enabled()
    svc = build_timeline_visualization_service()
    try:
        with session_scope() as session:
            track = svc.rebuild(session, body.creative_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return full_response(track)


@router.get("/scene/{scene_id}", response_model=ClipVisualInspectionOut)
def get_scene_visual_inspection(scene_id: str) -> ClipVisualInspectionOut:
    _require_enabled()
    creative_id, scene_index = _parse_scene_id(scene_id)
    svc = build_timeline_visualization_service()
    try:
        with session_scope() as session:
            ins = svc.get_scene_inspection(session, creative_id, scene_index)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return inspection_to_out(ins)


@router.get("/media/{creative_id}/scenes/{scene_index}/{kind}")
def serve_timeline_media(creative_id: str, scene_index: int, kind: str) -> FileResponse:
    _require_enabled()
    if kind not in ("thumbnail", "preview"):
        raise HTTPException(status_code=400, detail="invalid_media_kind")
    svc = build_timeline_visualization_service()
    try:
        with session_scope() as session:
            path = svc.resolve_media_path(session, creative_id, scene_index, kind=kind)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    if path is None:
        raise HTTPException(status_code=404, detail="timeline_media_not_found")
    media_type = "image/jpeg" if kind == "thumbnail" else "video/mp4"
    return FileResponse(path, media_type=media_type, filename=path.name)


@router.get("/media-url/{creative_id}/scenes/{scene_index}/{kind}")
def get_timeline_media_url(creative_id: str, scene_index: int, kind: str) -> dict[str, str]:
    """Devuelve URL relativa para el frontend (sin generar archivo)."""
    _require_enabled()
    if kind not in ("thumbnail", "preview"):
        raise HTTPException(status_code=400, detail="invalid_media_kind")
    return {"url": media_url(creative_id, scene_index, kind)}
