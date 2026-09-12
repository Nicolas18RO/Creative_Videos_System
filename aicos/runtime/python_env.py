"""Detección de intérprete Python y diagnóstico de dependencias Whisper."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parents[2]


def project_venv_python() -> Path | None:
    """Ruta al python del venv del repo (Windows: Scripts/python.exe)."""
    if sys.platform == "win32":
        candidate = _REPO_ROOT / ".venv" / "Scripts" / "python.exe"
    else:
        candidate = _REPO_ROOT / ".venv" / "bin" / "python"
    return candidate if candidate.is_file() else None


def is_project_venv_active() -> bool:
    venv_py = project_venv_python()
    if venv_py is None:
        return False
    try:
        return Path(sys.executable).resolve() == venv_py.resolve()
    except OSError:
        return False


def log_runtime_python_context() -> None:
    venv_py = project_venv_python()
    ver = sys.version_info
    logger.info("[Runtime] python_executable=%s version=%s.%s", sys.executable, ver.major, ver.minor)
    if ver.major != 3 or ver.minor != 11:
        logger.warning(
            "[Runtime] AI-COS está probado con Python 3.11 (pyproject: >=3.11,<3.12). "
            "Versión actual: %s.%s — usa el venv del repo si hay fallos con Whisper/torch.",
            ver.major,
            ver.minor,
        )
    if venv_py and not is_project_venv_active():
        logger.warning(
            "[Runtime] No estás usando el venv del proyecto (%s). "
            "Recomendado: scripts\\run_api.ps1 o %s -m uvicorn aicos.api.main:app --reload",
            sys.executable,
            venv_py,
        )


def format_whisper_import_failure(exc: BaseException) -> tuple[str, str]:
    """Devuelve (failure_reason, hint) para health checks y errores de analyze."""
    msg = str(exc).strip() or type(exc).__name__
    venv_py = project_venv_python()
    venv_hint = (
        f"{venv_py} -m pip install -e \".[ml]\""
        if venv_py
        else "python -m pip install -e \".[ml]\""
    )
    same_py = f"{sys.executable} -m pip install tokenizers huggingface-hub ctranslate2"

    if "No module named 'faster_whisper'" in msg or "faster_whisper" in msg and "No module named" in msg:
        return (
            msg,
            f"Instala el extra ML: {venv_hint} — o en este intérprete: {same_py} faster-whisper",
        )
    if "tokenizers" in msg:
        return (
            msg,
            "faster-whisper está instalado pero falta `tokenizers` en ESTE intérprete. "
            f"Opción A (recomendada): arrancar API con el venv → {venv_hint}. "
            f"Opción B: {same_py}",
        )
    if "ctranslate2" in msg:
        return (
            msg,
            f"Falta ctranslate2 (requerido por faster-whisper). Instala: {same_py} ctranslate2",
        )
    return (
        msg,
        f"Revisa dependencias ML con: {venv_hint}",
    )
