"""Keyframe medianoche vía FFmpeg (delega en ``FFmpegService``)."""

from __future__ import annotations

import logging
from pathlib import Path

from aicos.services.ffmpeg_service import FFmpegService

logger = logging.getLogger(__name__)


class FfmpegKeyframeExportAdapter:
    """Implementa ``KeyframeExportPort`` usando solo servicios de FFmpeg."""

    def __init__(self, *, ffmpeg: FFmpegService | None = None) -> None:
        self._ffmpeg = ffmpeg or FFmpegService()

    def export_median_frame(
        self,
        *,
        video_path: str,
        output_jpeg_path: str,
        width: int,
        height: int,
    ) -> bool:
        if not self._ffmpeg.is_available():
            logger.warning("[KeyframeExport] ffmpeg_unavailable")
            return False
        ok = self._ffmpeg.extract_thumbnail(
            Path(video_path),
            Path(output_jpeg_path),
            width=width,
            height=height,
            position=0.5,
        )
        return bool(ok)
