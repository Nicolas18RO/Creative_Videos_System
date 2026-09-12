"""GET /library/stats — estadísticas rápidas de la biblioteca indexada."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from aicos.database.db import ClipRow, session_scope
from aicos.models.schemas import LibraryClipsResponse
from aicos.services.library_service import library_stats, list_library_clips

router = APIRouter()


@router.get("/stats")
def get_stats() -> dict[str, int]:
    with session_scope() as session:
        return library_stats(session)


@router.get("/clips", response_model=LibraryClipsResponse)
def list_clips(
    limit: int = Query(50, ge=1, le=200, description="Tamaño de página"),
    offset: int = Query(0, ge=0, description="Desplazamiento para paginación"),
) -> LibraryClipsResponse:
    """Lista metadatos de clips (paginado, sin embeddings)."""
    with session_scope() as session:
        return list_library_clips(session, limit=limit, offset=offset)


@router.get("/clips/{clip_id}/thumbnail")
def get_clip_thumbnail(clip_id: str) -> FileResponse:
    """Sirve miniatura JPEG para UI web (Phase 7.1); sin lógica de ranking."""
    with session_scope() as session:
        clip = session.get(ClipRow, clip_id)
    if clip is None or not clip.thumbnail_path:
        raise HTTPException(status_code=404, detail="thumbnail_not_found")
    path = Path(clip.thumbnail_path).expanduser().resolve()
    if not path.is_file():
        raise HTTPException(status_code=404, detail="thumbnail_file_missing")
    return FileResponse(path, media_type="image/jpeg", filename=path.name)
