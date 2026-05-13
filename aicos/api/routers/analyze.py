"""POST /analyze — pipeline M1+M2+M3; GET /analyze/health — diagnóstico de dependencias."""

from __future__ import annotations

import logging
import time
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from aicos.database.db import session_scope
from aicos.models.schemas import AnalyzeAPIResponse, AnalyzeHealthResponse, AnalyzeRequestBody
from aicos.modules.script_analyzer import analyze_audio
from aicos.services import analyze_health_service, project_service
from aicos.services.analyze_exceptions import AnalyzePipelineError, wrap_stage_exception

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health", response_model=AnalyzeHealthResponse)
def analyze_health(
    probe_whisper_model: bool = Query(
        False,
        description="Si true, intenta cargar el modelo Whisper (lento; solo diagnóstico profundo).",
    ),
) -> AnalyzeHealthResponse:
    """Comprueba ffmpeg, whisper, embeddings, Chroma y SQLite."""
    logger.info("[Analyze] GET /analyze/health probe_whisper_model=%s", probe_whisper_model)
    return analyze_health_service.full_analyze_health(probe_whisper_model=probe_whisper_model)


@router.post("", response_model=AnalyzeAPIResponse)
async def analyze(body: AnalyzeRequestBody) -> AnalyzeAPIResponse:
    """Analiza un archivo de audio local (MP3/WAV) y devuelve escenas + clips + gaps."""
    t0 = time.perf_counter()
    logger.info(
        "[Analyze] POST entry persist=%s include_clip_search=%s enable_intelligence=%s project_name=%r",
        body.persist,
        body.include_clip_search,
        body.enable_intelligence,
        body.project_name,
    )

    try:
        p = Path(body.audio_path).expanduser().resolve()
    except Exception as e:
        logger.exception("[Analyze] Stage=router path resolution failed")
        wrapped = wrap_stage_exception("router", e)
        raise HTTPException(status_code=wrapped.http_status, detail=wrapped.to_detail_dict()) from e

    if not p.is_file():
        detail = {
            "stage": "router",
            "error_type": "FileNotFoundError",
            "message": f"Archivo no encontrado: {p}",
            "details": None,
            "recoverable": False,
        }
        logger.error("[Analyze] Stage=router %s", detail["message"])
        raise HTTPException(status_code=400, detail=detail)

    if p.stat().st_size <= 0:
        detail = {
            "stage": "router",
            "error_type": "InvalidAudio",
            "message": "El archivo de audio está vacío (0 bytes).",
            "details": str(p),
            "recoverable": False,
        }
        logger.error("[Analyze] Stage=router empty file")
        raise HTTPException(status_code=400, detail=detail)

    try:
        result = await analyze_audio(
            p,
            project_name=body.project_name,
            product_category=body.product_category,
            target_audience=body.target_audience,
            gender_hint_default=body.gender_hint_default,
            include_clip_search=body.include_clip_search,
            enable_intelligence=body.enable_intelligence,
        )
    except AnalyzePipelineError as e:
        logger.error(
            "[Analyze] pipeline_error stage=%s error_type=%s recoverable=%s msg=%s",
            e.stage,
            e.error_type,
            e.recoverable,
            e.message,
            exc_info=e.__cause__ is not None,
        )
        raise HTTPException(status_code=e.http_status, detail=e.to_detail_dict()) from e
    except Exception as e:
        logger.exception("[Analyze] unhandled pipeline exception")
        wrapped = wrap_stage_exception("pipeline", e)
        raise HTTPException(status_code=wrapped.http_status, detail=wrapped.to_detail_dict()) from e

    if body.persist:
        try:
            t1 = time.perf_counter()
            with session_scope() as session:
                project_service.persist_full_analysis(
                    session,
                    result,
                    audio_path=str(p),
                    product_name=body.product_name,
                    product_category=body.product_category,
                    target_audience=body.target_audience,
                )
            logger.info("[Analyze] Stage=persistence elapsed=%.3fs", time.perf_counter() - t1)
        except Exception as e:
            logger.exception("[Analyze] Stage=persistence FAILED")
            wrapped = wrap_stage_exception("persistence", e)
            raise HTTPException(status_code=wrapped.http_status, detail=wrapped.to_detail_dict()) from e

    logger.info("[Analyze] POST success total_elapsed=%.3fs scenes=%s", time.perf_counter() - t0, len(result.scenes))
    return result
