"""Puertos playback."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol

from aicos.domain.playback.entities import PlaybackSceneMap, WaveformPeaks


class PlaybackTimelineReadPort(Protocol):
    def load_scenes(self, session: Any, project_id: str) -> tuple[PlaybackSceneMap, ...]: ...


class PlaybackMediaPort(Protocol):
    def resolve_project_audio(self, session: Any, project_id: str) -> Path | None: ...

    def resolve_clip_video(self, session: Any, clip_id: str) -> Path | None: ...


class WaveformPort(Protocol):
    def extract(self, audio_path: Path, *, buckets: int = 320) -> WaveformPeaks: ...
