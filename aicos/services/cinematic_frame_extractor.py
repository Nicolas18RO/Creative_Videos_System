"""Adaptador FFmpeg para el puerto ``FrameExtractorPort`` (único lugar permitido para ffmpeg)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from aicos.services.ffmpeg_service import FFmpegService

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class FfmpegKeyframeExtractor:
    """Delega en ``FfmpegService.extract_keyframes``."""

    ffmpeg: FFmpegService
    cache_root: Path
    width: int = 320
    height: int = 180

    def extract_keyframe_paths(self, video_path: Path, max_frames: int) -> list[Path]:
        if not self.ffmpeg.is_available():
            logger.warning("metadata_generation stage=frame_extraction ffmpeg=unavailable")
            return []
        out_dir = self.cache_root / "cinematic_keyframes" / video_path.stem[:64]
        return self.ffmpeg.extract_keyframes(
            video_path,
            out_dir,
            max_frames=max_frames,
            width=self.width,
            height=self.height,
        )
