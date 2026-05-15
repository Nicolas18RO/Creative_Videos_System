"""Adaptador ffprobe vía servicio compartido de binarios (sin lógica editorial)."""

from __future__ import annotations

from pathlib import Path

from aicos.application.editorial_dataset.ports import VideoMetadataProbePort, VideoProbeResult
from aicos.services.ffmpeg_service import FFmpegService


class FfmpegVideoMetadataAdapter(VideoMetadataProbePort):
    def __init__(self, *, ffmpeg: FFmpegService | None = None) -> None:
        self._ffmpeg = ffmpeg or FFmpegService()

    def probe_media(self, path: Path) -> VideoProbeResult:
        meta = self._ffmpeg.get_video_metadata(path)
        return VideoProbeResult(
            duration_ms=meta.duration_ms,
            width=meta.width,
            height=meta.height,
        )
