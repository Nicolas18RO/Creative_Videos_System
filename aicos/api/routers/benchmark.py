
"""GET /benchmark/phase3 — evaluación baseline vs inteligencia."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query

from aicos.api.routers import search as search_mod
from aicos.database.db import session_scope
from aicos.models.schemas import Phase3BenchmarkResponse
from aicos.services import benchmark_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/phase3", response_model=Phase3BenchmarkResponse)
def phase3_benchmark(
    k: int = Query(5, ge=1, le=15),
    max_cases: int = Query(80, ge=1, le=200),
) -> Phase3BenchmarkResponse:
    emb, store = search_mod._get_clients()
    try:
        with session_scope() as session:
            return benchmark_service.run_phase3_benchmark(
                session, emb, store, k=k, max_cases=max_cases
            )
    except Exception as e:
        logger.exception("Benchmark Fase 3")
        raise HTTPException(status_code=500, detail=str(e)) from e
