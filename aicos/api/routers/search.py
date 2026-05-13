"""POST /search — búsqueda semántica M2."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from aicos.core.embedder import Embedder
from aicos.core.vector_store import VectorStore
from aicos.database.db import session_scope
from aicos.models.schemas import SearchRequest, SearchResponse
from aicos.modules.clip_recommender import recommend
from aicos.services import search_service

logger = logging.getLogger(__name__)
router = APIRouter()

_embedder: Embedder | None = None
_store: VectorStore | None = None


def _get_clients() -> tuple[Embedder, VectorStore]:
    global _embedder, _store
    if _embedder is None:
        try:
            _embedder = Embedder()
        except RuntimeError as e:
            raise HTTPException(status_code=503, detail=str(e)) from e
    if _store is None:
        _store = VectorStore()
    return _embedder, _store


@router.post("", response_model=SearchResponse)
def search(req: SearchRequest) -> SearchResponse:
    """Búsqueda semántica con boosting e inteligencia de uso opcional (índice vía bootstrap)."""
    emb, store = _get_clients()
    try:
        if req.record_usage or req.apply_intelligence:
            with session_scope() as session:
                return search_service.run_search(session, req, emb, store)
        return recommend(req, emb, store)
    except Exception as e:
        logger.exception("Fallo en búsqueda")
        raise HTTPException(status_code=500, detail=str(e)) from e
