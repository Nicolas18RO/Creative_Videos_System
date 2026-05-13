"""Errores estructurados del pipeline ``POST /analyze`` (API → cliente sin perder contexto)."""

from __future__ import annotations

import logging
import traceback
from typing import Any

logger = logging.getLogger(__name__)


class AnalyzePipelineError(Exception):
    """Fallo controlado del análisis con metadatos serializables a ``HTTPException.detail``."""

    def __init__(
        self,
        *,
        stage: str,
        error_type: str,
        message: str,
        details: str | None = None,
        recoverable: bool = False,
        http_status: int = 503,
    ) -> None:
        super().__init__(message)
        self.stage = stage
        self.error_type = error_type
        self.message = message
        self.details = details
        self.recoverable = recoverable
        self.http_status = http_status

    def to_detail_dict(self) -> dict[str, Any]:
        """Cuerpo JSON bajo la clave ``detail`` de FastAPI."""
        return {
            "stage": self.stage,
            "error_type": self.error_type,
            "message": self.message,
            "details": self.details,
            "recoverable": self.recoverable,
        }


def _tb_tail(exc: BaseException, *, max_chars: int = 8000) -> str:
    return "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))[-max_chars:]


def wrap_stage_exception(stage: str, exc: BaseException) -> AnalyzePipelineError:
    """Convierte una excepción arbitraria en ``AnalyzePipelineError`` con status HTTP razonable."""
    if isinstance(exc, AnalyzePipelineError):
        return exc

    name = type(exc).__name__
    msg = str(exc) or name
    tail = _tb_tail(exc)

    if isinstance(exc, MemoryError):
        return AnalyzePipelineError(
            stage=stage,
            error_type=name,
            message=msg,
            details=tail,
            recoverable=True,
            http_status=503,
        )

    try:
        import torch

        if isinstance(exc, torch.cuda.OutOfMemoryError):
            return AnalyzePipelineError(
                stage=stage,
                error_type=name,
                message=msg,
                details=tail,
                recoverable=True,
                http_status=503,
            )
    except ImportError:
        pass

    if isinstance(exc, FileNotFoundError):
        return AnalyzePipelineError(
            stage=stage,
            error_type=name,
            message=msg,
            details=tail,
            recoverable=False,
            http_status=400,
        )

    if isinstance(exc, (ValueError, PermissionError)):
        return AnalyzePipelineError(
            stage=stage,
            error_type=name,
            message=msg,
            details=tail,
            recoverable=False,
            http_status=400,
        )

    if isinstance(exc, ImportError):
        return AnalyzePipelineError(
            stage=stage,
            error_type=name,
            message=msg,
            details=tail,
            recoverable=True,
            http_status=503,
        )

    if isinstance(exc, OSError):
        low = msg.lower()
        recoverable = "chrom" in low or "connection" in low or "temporar" in low
        return AnalyzePipelineError(
            stage=stage,
            error_type=name,
            message=msg,
            details=tail,
            recoverable=recoverable,
            http_status=503 if recoverable or "no space" in low else 500,
        )

    if isinstance(exc, RuntimeError):
        low = msg.lower()
        recoverable = any(
            x in low
            for x in (
                "whisper",
                "faster-whisper",
                "cuda",
                "cudnn",
                "ffmpeg",
                "ffprobe",
                "chromadb",
                "chroma",
                "embedding",
                "openai",
                "api key",
                "no está instalado",
                "not installed",
            )
        )
        return AnalyzePipelineError(
            stage=stage,
            error_type=name,
            message=msg,
            details=tail,
            recoverable=recoverable,
            http_status=503,
        )

    mod = type(exc).__module__ or ""
    if "chromadb" in mod or "chroma" in name.lower():
        return AnalyzePipelineError(
            stage=stage,
            error_type=name,
            message=msg,
            details=tail,
            recoverable=True,
            http_status=503,
        )

    if "sqlalchemy" in mod or name in ("OperationalError", "IntegrityError", "DatabaseError"):
        return AnalyzePipelineError(
            stage=stage,
            error_type=name,
            message=msg,
            details=tail,
            recoverable=False,
            http_status=500,
        )

    if mod.startswith("sqlite3"):
        return AnalyzePipelineError(
            stage=stage,
            error_type=name,
            message=msg,
            details=tail,
            recoverable=False,
            http_status=500,
        )

    logger.exception("Excepción no clasificada en stage=%s", stage)
    return AnalyzePipelineError(
        stage=stage,
        error_type=name,
        message=msg,
        details=tail,
        recoverable=False,
        http_status=500,
    )
