"""Entidades puras de playback."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PlaybackState(str, Enum):
    IDLE = "idle"
    LOADING = "loading"
    READY = "ready"
    PLAYING = "playing"
    PAUSED = "paused"
    SEEKING = "seeking"
    SCENE_LOOP = "scene_loop"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class PlaybackSceneMap:
    scene_id: str
    scene_index: int
    start_sec: float
    end_sec: float
    duration_sec: float
    text: str
    concept: str
    narrative_function: str
    selected_clip_id: str | None


@dataclass(frozen=True, slots=True)
class PlaybackCue:
    """Subtítulo activo en un instante (calculado en dominio)."""

    scene_id: str
    scene_index: int
    text: str
    start_sec: float
    end_sec: float


@dataclass(frozen=True, slots=True)
class WaveformPeaks:
    duration_sec: float
    bucket_count: int
    peaks: tuple[float, ...]
