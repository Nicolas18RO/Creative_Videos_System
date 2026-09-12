"""Extracción y caché de picos de waveform vía ffmpeg (sin dependencias ML)."""

from __future__ import annotations

import hashlib
import json
import logging
import struct
import subprocess
from pathlib import Path

from aicos.config import get_config
from aicos.domain.playback.entities import WaveformPeaks
from aicos.services.ffmpeg_service import FFmpegService

logger = logging.getLogger(__name__)

DEFAULT_BUCKETS = 320


def _cache_path(audio_path: Path, buckets: int) -> Path:
    root = Path(get_config().resolved_paths().get("playback_cache", "~/.aicos/playback")).expanduser()
    root.mkdir(parents=True, exist_ok=True)
    h = hashlib.sha256(f"{audio_path}|{audio_path.stat().st_mtime}|{buckets}".encode()).hexdigest()[:24]
    return root / f"wf_{h}_{buckets}.json"


def extract_waveform_peaks(audio_path: Path, *, buckets: int = DEFAULT_BUCKETS) -> WaveformPeaks:
    """Genera picos normalizados 0..1; usa caché JSON en disco."""
    path = audio_path.expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(str(path))

    cache = _cache_path(path, buckets)
    if cache.is_file():
        try:
            data = json.loads(cache.read_text(encoding="utf-8"))
            return WaveformPeaks(
                duration_sec=float(data["duration_sec"]),
                bucket_count=int(data["bucket_count"]),
                peaks=tuple(float(x) for x in data["peaks"]),
            )
        except (json.JSONDecodeError, KeyError, TypeError):
            logger.warning("waveform cache corrupt, regenerating: %s", cache)

    ff = FFmpegService()
    if not ff.is_available():
        raise RuntimeError("ffmpeg no disponible para waveform")

    meta = ff.get_video_metadata(path)
    duration_sec = max(meta.duration_ms / 1000.0, 0.01)

    cmd = [
        ff._ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(path),
        "-ac",
        "1",
        "-ar",
        "8000",
        "-f",
        "f32le",
        "-",
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        raise RuntimeError(f"ffmpeg waveform extract failed: {e}") from e

    raw = proc.stdout
    if len(raw) < 4:
        peaks_tuple = tuple(0.0 for _ in range(buckets))
    else:
        n_samples = len(raw) // 4
        samples = struct.unpack(f"<{n_samples}f", raw[: n_samples * 4])
        peaks_list: list[float] = []
        chunk = max(1, n_samples // buckets)
        for i in range(buckets):
            start = i * chunk
            end = min(n_samples, start + chunk)
            if start >= end:
                peaks_list.append(0.0)
                continue
            peak = max(abs(samples[j]) for j in range(start, end))
            peaks_list.append(min(1.0, peak))
        mx = max(peaks_list) if peaks_list else 1.0
        if mx > 1e-9:
            peaks_list = [p / mx for p in peaks_list]
        peaks_tuple = tuple(peaks_list)

    wf = WaveformPeaks(duration_sec=duration_sec, bucket_count=buckets, peaks=peaks_tuple)
    cache.write_text(
        json.dumps(
            {
                "duration_sec": wf.duration_sec,
                "bucket_count": wf.bucket_count,
                "peaks": list(wf.peaks),
            }
        ),
        encoding="utf-8",
    )
    return wf
