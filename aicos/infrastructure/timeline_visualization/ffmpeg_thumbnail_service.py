"""Generación de thumbnails y previews MP4 vía FFmpeg (sin lógica editorial)."""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from shutil import which

from aicos.config import TimelineVisualizationConfig
from aicos.services.ffmpeg_service import FFmpegService

logger = logging.getLogger(__name__)


class FFmpegThumbnailService:
    """Cache en disco de miniaturas y previews cortos por creativo/escena."""

    def __init__(
        self,
        *,
        cfg: TimelineVisualizationConfig,
        cache_root: Path,
        ffmpeg: FFmpegService | None = None,
    ) -> None:
        self._cfg = cfg
        self._cache_root = cache_root
        self._ffmpeg = ffmpeg or FFmpegService()
        self._thumb_w, self._thumb_h = cfg.thumbnail_size

    def _creative_dir(self, creative_id: str) -> Path:
        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in creative_id)[:96]
        return self._cache_root / safe

    def _thumb_path(self, creative_id: str, scene_index: int) -> Path:
        return self._creative_dir(creative_id) / "thumbs" / f"scene_{scene_index:04d}.jpg"

    def _preview_path(self, creative_id: str, scene_index: int) -> Path:
        return self._creative_dir(creative_id) / "previews" / f"scene_{scene_index:04d}.mp4"

    def _contact_sheet_path(self, creative_id: str, scene_index: int) -> Path:
        return self._creative_dir(creative_id) / "sheets" / f"scene_{scene_index:04d}.jpg"

    def is_available(self) -> bool:
        return self._ffmpeg.is_available()

    def _seek_seconds(self, start_time: float, end_time: float) -> float:
        mid = (start_time + end_time) * 0.5
        return max(0.0, mid)

    def ensure_scene_thumbnail(
        self,
        *,
        source_video: Path,
        creative_id: str,
        scene_index: int,
        start_time: float,
        end_time: float,
    ) -> Path | None:
        out = self._thumb_path(creative_id, scene_index)
        if out.is_file() and not self._cfg.regenerate_on_request:
            return out
        if not source_video.is_file():
            return None
        ss = self._seek_seconds(start_time, end_time)
        out.parent.mkdir(parents=True, exist_ok=True)
        if self._extract_frame_at(source_video, out, ss, self._thumb_w, self._thumb_h):
            return out
        return None

    def ensure_scene_preview(
        self,
        *,
        source_video: Path,
        creative_id: str,
        scene_index: int,
        start_time: float,
        end_time: float,
    ) -> Path | None:
        out = self._preview_path(creative_id, scene_index)
        if out.is_file() and not self._cfg.regenerate_on_request:
            return out
        if not source_video.is_file() or not which(self._ffmpeg._ffmpeg):
            return None
        seg = max(0.05, end_time - start_time)
        dur = min(float(self._cfg.preview_max_seconds), max(float(self._cfg.preview_min_seconds), seg))
        ss = max(0.0, start_time)
        out.parent.mkdir(parents=True, exist_ok=True)
        vf = (
            f"scale={self._cfg.preview_width}:{self._cfg.preview_height}:"
            "force_original_aspect_ratio=decrease,"
            f"pad={self._cfg.preview_width}:{self._cfg.preview_height}:(ow-iw)/2:(oh-ih)/2"
        )
        cmd = [
            self._ffmpeg._ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            f"{ss:.3f}",
            "-i",
            str(source_video),
            "-t",
            f"{dur:.3f}",
            "-an",
            "-vf",
            vf,
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            str(self._cfg.preview_crf),
            "-movflags",
            "+faststart",
            str(out),
            "-y",
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            return out if out.is_file() else None
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.warning("preview ffmpeg failed creative=%s scene=%s: %s", creative_id, scene_index, e)
            return None

    def ensure_contact_sheet(
        self,
        *,
        source_video: Path,
        creative_id: str,
        scene_index: int,
        start_time: float,
        end_time: float,
        frames: int = 4,
    ) -> Path | None:
        out = self._contact_sheet_path(creative_id, scene_index)
        if out.is_file():
            return out
        if not source_video.is_file():
            return None
        seg = max(0.1, end_time - start_time)
        n = max(1, min(frames, 6))
        tmp = self._creative_dir(creative_id) / "sheets" / f"_tmp_{scene_index:04d}"
        tmp.mkdir(parents=True, exist_ok=True)
        paths: list[Path] = []
        for i in range(n):
            t = start_time + (i + 0.5) * seg / n
            p = tmp / f"f{i}.jpg"
            if self._extract_frame_at(source_video, p, t, self._thumb_w, self._thumb_h):
                paths.append(p)
        if not paths:
            return None
        out.parent.mkdir(parents=True, exist_ok=True)
        if len(paths) == 1:
            paths[0].replace(out)
            return out
        try:
            inputs: list[str] = []
            for p in paths:
                inputs.extend(["-i", str(p)])
            filt = "".join(f"[{i}:v]scale={self._thumb_w}:{self._thumb_h}[v{i}];" for i in range(len(paths)))
            stack = "".join(f"[v{i}]" for i in range(len(paths)))
            filt += f"{stack}hstack=inputs={len(paths)}[out]"
            cmd = [
                self._ffmpeg._ffmpeg,
                "-hide_banner",
                "-loglevel",
                "error",
                *inputs,
                "-filter_complex",
                filt,
                "-map",
                "[out]",
                "-frames:v",
                "1",
                str(out),
                "-y",
            ]
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            return out if out.is_file() else None
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.warning("contact sheet failed: %s", e)
            return None

    def _extract_frame_at(self, video: Path, output: Path, ss: float, w: int, h: int) -> bool:
        output.parent.mkdir(parents=True, exist_ok=True)
        vf = f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2"
        cmd = [
            self._ffmpeg._ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            f"{ss:.3f}",
            "-i",
            str(video),
            "-vframes",
            "1",
            "-vf",
            vf,
            "-q:v",
            "3",
            str(output),
            "-y",
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            return output.is_file()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def purge_creative_cache(self, creative_id: str) -> None:
        d = self._creative_dir(creative_id)
        if d.is_dir():
            import shutil

            shutil.rmtree(d, ignore_errors=True)
