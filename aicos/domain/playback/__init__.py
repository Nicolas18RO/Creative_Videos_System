"""Motor de playback cinematográfico (Phase 7.3)."""

from aicos.domain.playback.entities import PlaybackCue, PlaybackSceneMap, PlaybackState, WaveformPeaks
from aicos.domain.playback.rules import (
    active_scene_at_time,
    can_transition,
    clamp_time,
    scene_local_time,
)

__all__ = [
    "PlaybackCue",
    "PlaybackSceneMap",
    "PlaybackState",
    "WaveformPeaks",
    "active_scene_at_time",
    "can_transition",
    "clamp_time",
    "scene_local_time",
]
