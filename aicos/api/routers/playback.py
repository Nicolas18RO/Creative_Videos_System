"""Playback studio — streaming y sesión (Phase 7.3)."""

from __future__ import annotations

import mimetypes

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse

from aicos.application.playback.presentation import session_to_out
from aicos.database.db import ProjectRow, session_scope
from aicos.infrastructure.playback.media_resolver import SqlPlaybackMediaResolver
from aicos.infrastructure.playback.waveform_extractor import extract_waveform_peaks
from aicos.services.playback_factory import build_playback_session_service

router = APIRouter()
_media = SqlPlaybackMediaResolver()


def _guess_media_type(path) -> str:
    mt, _ = mimetypes.guess_type(str(path))
    return mt or "application/octet-stream"


@router.get("/projects/{project_id}/session")
def get_playback_session(project_id: str):
    svc = build_playback_session_service()
    with session_scope() as session:
        proj = session.get(ProjectRow, project_id)
        if proj is None:
            raise HTTPException(status_code=404, detail="project_not_found")
        bundle = svc.build_session(session, project_id, proj.name or "Proyecto")
    return session_to_out(bundle)


@router.get("/projects/{project_id}/audio")
def stream_project_audio(project_id: str):
    with session_scope() as session:
        path = _media.resolve_project_audio(session, project_id)
    if path is None:
        raise HTTPException(status_code=404, detail="project_audio_not_found")
    return FileResponse(path, media_type=_guess_media_type(path), filename=path.name)


@router.get("/clips/{clip_id}/stream")
def stream_clip_video(clip_id: str):
    with session_scope() as session:
        path = _media.resolve_clip_video(session, clip_id)
    if path is None:
        raise HTTPException(status_code=404, detail="clip_not_found")
    return FileResponse(path, media_type=_guess_media_type(path), filename=path.name)


@router.get("/projects/{project_id}/waveform")
def get_project_waveform(project_id: str):
    with session_scope() as session:
        path = _media.resolve_project_audio(session, project_id)
        if path is None:
            raise HTTPException(status_code=404, detail="project_audio_not_found")
        try:
            wf = extract_waveform_peaks(path)
        except Exception as e:
            raise HTTPException(status_code=503, detail=str(e)) from e
    return JSONResponse(
        {
            "duration_sec": wf.duration_sec,
            "bucket_count": wf.bucket_count,
            "peaks": list(wf.peaks),
        }
    )
