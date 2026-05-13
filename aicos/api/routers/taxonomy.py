"""Endpoints de taxonomía (reclasificación sugerida, sin escritura automática)."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from aicos.database.db import session_scope
from aicos.models.schemas import ReclassificationBatchRequest, ReclassificationBatchResponse
from aicos.services import reclassification_pipeline

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/reclassify/batch", response_model=ReclassificationBatchResponse)
async def reclassify_batch(body: ReclassificationBatchRequest) -> ReclassificationBatchResponse:
    """Sugerencias M4 para clips marcados; no modifica SQLite."""
    try:
        with session_scope() as session:
            return await reclassification_pipeline.run_batch(session, body)
    except Exception as e:
        logger.exception("Batch reclasificación")
        raise HTTPException(status_code=500, detail=str(e)) from e
