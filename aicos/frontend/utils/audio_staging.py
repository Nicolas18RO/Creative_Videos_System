"""Copia segura de audio arrastrado a caché local (~/.aicos/cache/audio)."""

from __future__ import annotations

import logging
import shutil
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)


def stage_audio_file(src_path: str) -> str:
    """Copia ``src_path`` a ``~/.aicos/cache/audio/{uuid}_{nombre}`` y devuelve la ruta destino.

    No modifica el archivo original. Crea directorios si faltan. Evita colisiones con UUID.

    Args:
        src_path: Ruta absoluta o relativa al archivo de audio existente.

    Returns:
        Ruta absoluta del archivo copiado en caché.

    Raises:
        FileNotFoundError: Si el origen no existe.
        ValueError: Si la extensión no es soportada o la copia falla.
    """
    src = Path(src_path).expanduser().resolve()
    if not src.is_file():
        raise FileNotFoundError(f"No existe archivo de audio: {src}")

    ext = src.suffix.lower()
    if ext not in {".mp3", ".wav"}:
        raise ValueError(f"Extensión no permitida para staging: {ext}")

    cache_dir = Path.home() / ".aicos" / "cache" / "audio"
    cache_dir.mkdir(parents=True, exist_ok=True)

    safe_name = src.name
    dest_name = f"{uuid.uuid4().hex}_{safe_name}"
    dest = cache_dir / dest_name

    if dest.exists():
        dest = cache_dir / f"{uuid.uuid4().hex}_{uuid.uuid4().hex}_{safe_name}"

    try:
        shutil.copy2(src, dest)
    except OSError as ex:
        logger.exception("Fallo al copiar audio a caché: %s -> %s", src, dest)
        raise ValueError(f"No se pudo copiar el audio a caché: {ex}") from ex

    logger.info("Audio staged: %s -> %s", src, dest)
    return str(dest)
