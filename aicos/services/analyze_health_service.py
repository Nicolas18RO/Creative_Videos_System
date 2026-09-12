"""Comprobaciones de dependencias para ``POST /analyze`` y ``GET /analyze/health``."""

from __future__ import annotations

import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from sqlalchemy import text

from aicos.config import get_config
from aicos.database.db import get_engine
from aicos.models.schemas import AnalyzeHealthCheck, AnalyzeHealthResponse
from aicos.runtime.python_env import format_whisper_import_failure, is_project_venv_active
from aicos.services.ffmpeg_service import FFmpegService

logger = logging.getLogger(__name__)


def _check(
    name: str,
    ok: bool,
    message: str = "",
    *,
    recoverable: bool = True,
    failure_reason: str | None = None,
    **extra: Any,
) -> AnalyzeHealthCheck:
    """Construye un ítem de health con ``status`` y ``failure_reason`` explícitos."""
    status: Literal["pass", "fail", "skipped"] = "pass" if ok else "fail"
    fr = None if ok else (failure_reason or message or "Comprobación fallida")
    details = {k: v for k, v in extra.items() if v is not None}
    return AnalyzeHealthCheck(
        name=name,
        ok=ok,
        status=status,
        message=message or None,
        failure_reason=fr,
        recoverable=recoverable,
        details=details or None,
    )


def _finalize(checks: list[AnalyzeHealthCheck]) -> AnalyzeHealthResponse:
    ok = all(c.ok for c in checks)
    failed = [c for c in checks if not c.ok]
    if ok:
        summary = "Todas las comprobaciones pasaron."
        overall: Literal["healthy", "unhealthy"] = "healthy"
    else:
        parts = [f"{c.name} ({c.failure_reason or c.message or 'sin detalle'})" for c in failed]
        summary = "Fallos: " + "; ".join(parts)
        overall = "unhealthy"
    return AnalyzeHealthResponse(
        ok=ok,
        overall_status=overall,
        summary=summary,
        checks=checks,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


def validate_ffmpeg() -> AnalyzeHealthCheck:
    """Comprueba que ``ffmpeg`` y ``ffprobe`` estén en PATH (útil para decodificación de audio)."""
    svc = FFmpegService()
    ok = svc.is_available()
    return _check(
        "ffmpeg",
        ok,
        "ffmpeg y ffprobe disponibles en PATH" if ok else "ffmpeg o ffprobe no encontrados en PATH",
        recoverable=True,
        failure_reason=None
        if ok
        else "Instala FFmpeg y asegúrate de que `ffmpeg` y `ffprobe` estén en el PATH del proceso del servidor.",
        ffmpeg=svc._ffmpeg,
        ffprobe=svc._ffprobe,
    )


def validate_whisper(*, probe_model_load: bool = False) -> AnalyzeHealthCheck:
    """Comprueba import de faster-whisper y (opcional) carga del modelo configurado."""
    t0 = time.perf_counter()
    cfg = get_config().transcription
    try:
        from faster_whisper import WhisperModel
    except ImportError as e:
        failure_reason, hint = format_whisper_import_failure(e)
        return _check(
            "whisper",
            False,
            message="faster-whisper no está instalado o no se puede importar",
            failure_reason=failure_reason,
            recoverable=True,
            model=cfg.model,
            device=cfg.device,
            python_executable=sys.executable,
            using_project_venv=is_project_venv_active(),
            hint=hint,
            elapsed_ms=int((time.perf_counter() - t0) * 1000),
        )
    except OSError as e:
        logger.warning("faster-whisper: error al cargar biblioteca nativa (DLL/so): %s", e)
        return _check(
            "whisper",
            False,
            message="Biblioteca nativa de faster-whisper no cargable",
            failure_reason=str(e),
            recoverable=True,
            model=cfg.model,
            device=cfg.device,
            error_type=type(e).__name__,
            hint="En Windows: instala Visual C++ Redistributable; revisa antivirus bloqueando DLLs.",
            elapsed_ms=int((time.perf_counter() - t0) * 1000),
        )

    if not probe_model_load:
        return _check(
            "whisper",
            True,
            "faster-whisper importable; carga del modelo no probada (usa ?probe_whisper_model=true)",
            recoverable=True,
            model=cfg.model,
            device=cfg.device,
            elapsed_ms=int((time.perf_counter() - t0) * 1000),
        )

    try:
        model = WhisperModel(cfg.model, device=cfg.device, compute_type="int8")
        del model
        return _check(
            "whisper",
            True,
            "Modelo Whisper cargado correctamente",
            recoverable=True,
            model=cfg.model,
            device=cfg.device,
            elapsed_ms=int((time.perf_counter() - t0) * 1000),
        )
    except Exception as e:
        logger.exception("validate_whisper probe_model_load falló")
        return _check(
            "whisper",
            False,
            message="No se pudo cargar el modelo Whisper configurado",
            failure_reason=str(e),
            recoverable=True,
            model=cfg.model,
            device=cfg.device,
            error_type=type(e).__name__,
            elapsed_ms=int((time.perf_counter() - t0) * 1000),
        )


def validate_embeddings_pipeline() -> AnalyzeHealthCheck:
    """Intenta construir un ``Embedder`` (sentence-transformers u OpenAI según config)."""
    t0 = time.perf_counter()
    try:
        from aicos.core.embedder import Embedder

        emb = Embedder()
        dim = emb.embedding_dimension
        return _check(
            "embeddings",
            True,
            "Proveedor de embeddings operativo",
            recoverable=True,
            dimension=dim,
            elapsed_ms=int((time.perf_counter() - t0) * 1000),
        )
    except Exception as e:
        logger.exception("validate_embeddings_pipeline falló")
        return _check(
            "embeddings",
            False,
            message="No se pudo inicializar el proveedor de embeddings",
            failure_reason=str(e),
            recoverable=True,
            error_type=type(e).__name__,
            elapsed_ms=int((time.perf_counter() - t0) * 1000),
        )


def validate_vector_store() -> AnalyzeHealthCheck:
    """Abre Chroma persistente y obtiene/crea la colección de clips."""
    t0 = time.perf_counter()
    try:
        from aicos.core.vector_store import VectorStore, get_clip_collection_name

        vs = VectorStore()
        name = vs.collection_name or get_clip_collection_name()
        return _check(
            "vector_store",
            True,
            "ChromaDB accesible",
            recoverable=True,
            collection=name,
            path=str(vs._path),
            elapsed_ms=int((time.perf_counter() - t0) * 1000),
        )
    except Exception as e:
        logger.exception("validate_vector_store falló")
        return _check(
            "vector_store",
            False,
            message="ChromaDB no accesible o colección no disponible",
            failure_reason=str(e),
            recoverable=True,
            error_type=type(e).__name__,
            elapsed_ms=int((time.perf_counter() - t0) * 1000),
        )


def validate_sqlite() -> AnalyzeHealthCheck:
    """Usa el mismo singleton que ``session_scope`` (``get_engine``) y valida conexión con ``SELECT 1``."""
    t0 = time.perf_counter()
    try:
        eng = get_engine()
        raw = str(eng.url)
        with eng.connect() as conn:
            one = conn.scalar(text("SELECT 1"))
        if one != 1:
            return _check(
                "sqlite",
                False,
                message="Consulta de prueba a SQLite devolvió un valor inesperado",
                failure_reason=f"SELECT 1 → {one!r}",
                recoverable=False,
                database_url_prefix=raw[:120],
                elapsed_ms=int((time.perf_counter() - t0) * 1000),
            )
        return _check(
            "sqlite",
            True,
            "SQLite accesible (mismo motor que session_scope)",
            recoverable=True,
            database_url_prefix=raw[:120],
            elapsed_ms=int((time.perf_counter() - t0) * 1000),
        )
    except Exception as e:
        logger.exception("validate_sqlite falló")
        return _check(
            "sqlite",
            False,
            message="No se pudo conectar a la base SQLite configurada",
            failure_reason=str(e),
            recoverable=False,
            error_type=type(e).__name__,
            elapsed_ms=int((time.perf_counter() - t0) * 1000),
        )


def validate_audio_readable(path: str | Path) -> AnalyzeHealthCheck:
    """Comprueba que exista un archivo de audio local (opcional para diagnóstico puntual)."""
    p = Path(path).expanduser().resolve()
    if not p.is_file():
        return _check(
            "audio_file",
            False,
            "Archivo inexistente",
            recoverable=False,
            failure_reason=f"No existe: {p}",
            path=str(p),
            extension=p.suffix.lower(),
            size_bytes=0,
        )
    size = p.stat().st_size
    ok = size > 0
    return _check(
        "audio_file",
        ok,
        f"Archivo legible ({p})" if ok else "Archivo vacío (0 bytes)",
        recoverable=False,
        failure_reason=None if ok else "El archivo tiene 0 bytes",
        path=str(p),
        extension=p.suffix.lower(),
        size_bytes=size,
    )


def validate_audio_pipeline(*, probe_whisper_model: bool = False) -> AnalyzeHealthResponse:
    """Agregado: ffmpeg + whisper + sqlite (sin embeddings/Chroma)."""
    checks = [
        validate_ffmpeg(),
        validate_whisper(probe_model_load=probe_whisper_model),
        validate_sqlite(),
    ]
    return _finalize(checks)


def full_analyze_health(*, probe_whisper_model: bool = False) -> AnalyzeHealthResponse:
    """Todas las comprobaciones relevantes para ``POST /analyze`` con búsqueda de clips."""
    checks = [
        validate_ffmpeg(),
        validate_whisper(probe_model_load=probe_whisper_model),
        validate_embeddings_pipeline(),
        validate_vector_store(),
        validate_sqlite(),
    ]
    return _finalize(checks)


def log_startup_analyze_readiness() -> None:
    """Registra un resumen ligero al arranque (sin cargar modelo Whisper por defecto)."""
    try:
        snap = validate_audio_pipeline(probe_whisper_model=False)
        if snap.ok:
            logger.info("[AnalyzeHealth] startup OK summary=%r checks=%s", snap.summary, [c.name for c in snap.checks])
        else:
            failed = [c.name for c in snap.checks if not c.ok]
            logger.warning(
                "[AnalyzeHealth] startup issues overall=%s failed=%s summary=%r",
                snap.overall_status,
                failed,
                snap.summary,
            )
    except Exception as e:
        logger.warning("[AnalyzeHealth] startup validation skipped: %s", e)
