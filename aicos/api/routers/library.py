"""GET /library/stats — estadísticas rápidas de la biblioteca indexada."""

from __future__ import annotations

from fastapi import APIRouter, Query

from aicos.database.db import session_scope
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
