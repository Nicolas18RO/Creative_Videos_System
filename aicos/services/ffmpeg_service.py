"""Extracción de thumbnails y metadatos vía FFmpeg (subprocess)."""

from __future__ import annotations

import hashlib
import json
import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path
from shutil import which

logger = logging.getLogger(__name__)


@dataclass
class VideoMetadata:
    """Metadatos básicos de un archivo de video o audio."""

    duration_ms: int
    width: int | None
    height: int | None
    codec: str | None
    fps: float | None
    file_size_bytes: int


class FFmpegService:
    """Wrapper mínimo sobre la CLI de `ffmpeg`/`ffprobe`."""

    def __init__(self, ffmpeg_bin: str = "ffmpeg", ffprobe_bin: str = "ffprobe") -> None:
        self._ffmpeg = ffmpeg_bin
        self._ffprobe = ffprobe_bin

    def is_available(self) -> bool:
        return which(self._ffmpeg) is not None and which(self._ffprobe) is not None

    def compute_file_hash(self, file_path: Path) -> str:
        """Calcula SHA256 del archivo en bloques."""
        h = hashlib.sha256()
        with file_path.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()

    def get_video_metadata(self, video_path: Path) -> VideoMetadata:
        """Lee duración y dimensiones con ffprobe."""
        cmd = [
            self._ffprobe,
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(video_path),
        ]
        try:
            out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.warning("ffprobe falló para %s: %s", video_path, e)
            return VideoMetadata(
                duration_ms=0,
                width=None,
                height=None,
                codec=None,
                fps=None,
                file_size_bytes=video_path.stat().st_size,
            )
        data = json.loads(out)
        fmt = data.get("format") or {}
        duration_s = float(fmt.get("duration") or 0.0)
        duration_ms = int(duration_s * 1000)
        width = height = None
        codec = None
        fps = None
        for st in data.get("streams") or []:
            if st.get("codec_type") == "video" and width is None:
                width = int(st.get("width") or 0) or None
                height = int(st.get("height") or 0) or None
                codec = st.get("codec_name")
                fr = st.get("avg_frame_rate") or "0/1"
                if "/" in fr:
                    a, b = fr.split("/", 1)
                    fps = float(a) / float(b) if float(b) else None
                break
        return VideoMetadata(
            duration_ms=duration_ms,
            width=width,
            height=height,
            codec=codec,
            fps=fps,
            file_size_bytes=video_path.stat().st_size,
        )

    def extract_thumbnail(
        self,
        video_path: Path,
        output_path: Path,
        width: int = 160,
        height: int = 90,
        position: float = 0.5,
    ) -> bool:
        """Genera un JPEG de miniatura; retorna True si tuvo éxito."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        meta = self.get_video_metadata(video_path)
        ss = 1.0
        if meta.duration_ms > 0:
            ss = max(0.0, min(meta.duration_ms / 1000.0 * position, meta.duration_ms / 1000.0 - 0.05))
        vf = (
            f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2"
        )
        cmd = [
            self._ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            f"{ss:.3f}",
            "-i",
            str(video_path),
            "-vframes",
            "1",
            "-vf",
            vf,
            "-q:v",
            "3",
            str(output_path),
            "-y",
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            return output_path.is_file()
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.warning("ffmpeg thumbnail falló para %s: %s", video_path, e)
            return False

    def extract_keyframes(
        self,
        video_path: Path,
        output_dir: Path,
        max_frames: int = 4,
        width: int = 320,
        height: int = 180,
    ) -> list[Path]:
        """Extrae hasta ``max_frames`` JPEG espaciados en el timeline (para análisis visual local).

        Args:
            video_path: Ruta al vídeo.
            output_dir: Carpeta de salida (se crea si no existe).
            max_frames: Máximo de fotogramas (mínimo 1).
            width: Ancho escalado.
            height: Alto escalado.

        Returns:
            Rutas de archivos creados (puede ser vacía si falla ffmpeg o el vídeo).
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        if max_frames < 1:
            return []
        meta = self.get_video_metadata(video_path)
        duration_s = max(meta.duration_ms / 1000.0, 0.1)
        n = min(max_frames, 12)
        positions = [min(0.95, (i + 0.5) / n) for i in range(n)]
        vf = (
            f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2"
        )
        out_paths: list[Path] = []
        stem = video_path.stem[:80]
        for i, pos in enumerate(positions):
            ss = max(0.0, min(duration_s * pos, duration_s - 0.05))
            out_path = output_dir / f"{stem}_kf_{i:02d}.jpg"
            cmd = [
                self._ffmpeg,
                "-hide_banner",
                "-loglevel",
                "error",
                "-ss",
                f"{ss:.3f}",
                "-i",
                str(video_path),
                "-vframes",
                "1",
                "-vf",
                vf,
                "-q:v",
                "3",
                str(out_path),
                "-y",
            ]
            try:
                subprocess.run(cmd, check=True, capture_output=True, text=True)
                if out_path.is_file():
                    out_paths.append(out_path)
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                logger.warning("ffmpeg keyframe %s falló para %s: %s", i, video_path, e)
        return out_paths
