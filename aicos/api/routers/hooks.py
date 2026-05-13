"""GET /hooks/search — Hook Library (Fase 3 PRD)."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query

from aicos.api.routers import search as search_mod
from aicos.database.db import session_scope
from aicos.models.schemas import HookSearchResponse
from aicos.services import hook_library_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/search", response_model=HookSearchResponse)
def hooks_search(
    q: str = Query(..., min_length=1, description="Texto de búsqueda semántica"),
    n_results: int = Query(8, ge=1, le=20),
    candidate_pool_size: int = Query(24, ge=8, le=60),
) -> HookSearchResponse:
    emb, store = search_mod._get_clients()
    try:
        with session_scope() as session:
            return hook_library_service.search_hooks(
                session,
                query=q,
                embedder=emb,
                store=store,
                n_results=n_results,
                candidate_pool_size=candidate_pool_size,
            )
    except Exception as e:
        logger.exception("Hook search")
        raise HTTPException(status_code=500, detail=str(e)) from e
