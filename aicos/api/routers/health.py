"""Healthcheck y comprobaciones de entorno."""

from __future__ import annotations

import logging

from fastapi import APIRouter
from sqlalchemy import text

from aicos.config import get_config
from aicos.core.vector_store import VectorStore
from aicos.database.db import get_engine
from aicos.services.ffmpeg_service import FFmpegService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/ready")
def health_ready() -> dict:
    """Comprueba SQLite, carpeta de Chroma y ffmpeg (útil en despliegue local)."""
    checks: dict[str, bool | str] = {}
    ok = True

    try:
        eng = get_engine()
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception as e:
        logger.warning("DB check: %s", e)
        checks["database"] = False
        ok = False

    try:
        cfg = get_config()
        paths = cfg.resolved_paths()
        checks["vector_store_path"] = str(paths["vector_store"])
        checks["embeddings_provider"] = cfg.embeddings.provider
        checks["embeddings_model"] = cfg.embeddings.model
        _ = VectorStore()
        checks["vector_store"] = True
    except Exception as e:
        logger.warning("Chroma check: %s", e)
        checks["vector_store"] = False
        ok = False

    ff = FFmpegService()
    checks["ffmpeg"] = ff.is_available()

    status = "ready" if ok and checks.get("ffmpeg") else "degraded"
    return {"status": status, "checks": checks}
