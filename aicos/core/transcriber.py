"""Transcripción local con faster-whisper (M1)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from aicos.config import get_config
from aicos.models.schemas import Transcript, TranscriptSegment, TranscriptWord

logger = logging.getLogger(__name__)

_model_singleton: Any = None


def _get_model():
    global _model_singleton
    if _model_singleton is not None:
        return _model_singleton
    try:
        from faster_whisper import WhisperModel
    except ImportError as e:
        logger.exception("faster-whisper no importable")
        raise RuntimeError(
            "faster-whisper no está instalado. Instala el extra: pip install 'aicos[ml]'"
        ) from e
    cfg = get_config().transcription
    logger.info(
        "Cargando modelo Whisper %s (device=%s)…",
        cfg.model,
        cfg.device,
    )
    try:
        _model_singleton = WhisperModel(
            cfg.model,
            device=cfg.device,
            compute_type="int8",
        )
    except MemoryError:
        logger.exception("OOM al cargar modelo Whisper")
        raise
    except Exception as e:
        logger.exception("Fallo al instanciar WhisperModel: %s", e)
        raise RuntimeError(
            f"No se pudo cargar el modelo Whisper ({cfg.model!r}): {e}. "
            "Comprueba disco, VRAM/RAM y que el nombre del modelo sea válido."
        ) from e
    return _model_singleton


def transcribe(audio_path: str | Path) -> Transcript:
    """Transcribe un MP3/WAV con timestamps por palabra cuando el modelo lo permite.

    Args:
        audio_path: Ruta al archivo de audio.

    Returns:
        Transcript con segmentos y palabras en milisegundos.

    Raises:
        FileNotFoundError: Si el archivo no existe.
        RuntimeError: Si faster-whisper falla (modelo, CUDA, ffmpeg, audio corrupto).
        MemoryError: Si hay falta de memoria durante inferencia.
    """
    path = Path(audio_path).resolve()
    if not path.is_file():
        raise FileNotFoundError(str(path))

    cfg = get_config().transcription
    model = _get_model()

    try:
        segments_gen, info = model.transcribe(
            str(path),
            language=cfg.language,
            word_timestamps=bool(cfg.word_timestamps),
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 500},
        )
    except MemoryError:
        logger.exception("OOM durante model.transcribe path=%s", path)
        raise
    except Exception as e:
        logger.exception("model.transcribe falló path=%s", path)
        low = str(e).lower()
        if "ffmpeg" in low or "ffprobe" in low:
            raise RuntimeError(
                "FFmpeg/ffprobe requerido para decodificar audio con faster-whisper. "
                f"Detalle: {e}"
            ) from e
        if "cuda" in low or "cudnn" in low:
            raise RuntimeError(
                f"Error de GPU/CUDA durante transcripción: {e}. Prueba device=cpu en config."
            ) from e
        raise RuntimeError(f"Transcripción fallida: {e}") from e

    out_segments: list[TranscriptSegment] = []
    full_parts: list[str] = []

    try:
        for seg in segments_gen:
            text = (seg.text or "").strip()
            if not text:
                continue
            start_ms = int(seg.start * 1000)
            end_ms = int(seg.end * 1000)
            words: list[TranscriptWord] = []
            if getattr(seg, "words", None):
                for w in seg.words:
                    wtxt = (getattr(w, "word", None) or "").strip()
                    if not wtxt:
                        continue
                    words.append(
                        TranscriptWord(
                            start_ms=int(w.start * 1000),
                            end_ms=int(w.end * 1000),
                            word=wtxt,
                        )
                    )
            out_segments.append(
                TranscriptSegment(start_ms=start_ms, end_ms=end_ms, text=text, words=words)
            )
            full_parts.append(text)
    except Exception as e:
        logger.exception("Error procesando segmentos Whisper")
        raise RuntimeError(f"Salida de Whisper inválida o incompleta: {e}") from e

    duration_ms = int((info.duration or 0) * 1000)
    if not out_segments:
        logger.warning("Transcripción sin segmentos de texto (audio vacío o solo silencio): %s", path)
        return Transcript(
            full_text="",
            language=info.language or (cfg.language or "es"),
            segments=[],
            duration_ms=duration_ms,
            audio_path=str(path),
        )

    if duration_ms <= 0:
        duration_ms = out_segments[-1].end_ms

    return Transcript(
        full_text=" ".join(full_parts).strip(),
        language=info.language or (cfg.language or "es"),
        segments=out_segments,
        duration_ms=duration_ms,
        audio_path=str(path),
    )
