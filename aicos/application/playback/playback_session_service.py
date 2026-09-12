"""Construye sesión de playback para un proyecto."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aicos.application.playback.ports import PlaybackMediaPort, PlaybackTimelineReadPort, WaveformPort
from aicos.domain.cinematic_timeline.entities import ProjectTimelineScene
from aicos.domain.playback.entities import PlaybackSceneMap, WaveformPeaks
from aicos.infrastructure.cinematic_timeline.sql_project_timeline_repository import (
    SqlProjectTimelineRepository,
)


@dataclass(frozen=True, slots=True)
class PlaybackSessionBundle:
    project_id: str
    project_name: str
    duration_sec: float
    scenes: tuple[PlaybackSceneMap, ...]
    waveform: WaveformPeaks | None
    has_project_audio: bool
    has_waveform: bool


class PlaybackTimelineAdapter:
    """Adapta timeline de proyecto a mapas de playback."""

    def __init__(self, repo: SqlProjectTimelineRepository | None = None) -> None:
        self._repo = repo or SqlProjectTimelineRepository()

    def load_scenes(self, session: Any, project_id: str) -> tuple[PlaybackSceneMap, ...]:
        rows = self._repo.load_timeline(session, project_id)
        return tuple(self._map_row(r) for r in rows)

    @staticmethod
    def _map_row(r: ProjectTimelineScene) -> PlaybackSceneMap:
        start = r.start_ms / 1000.0
        end = r.end_ms / 1000.0
        return PlaybackSceneMap(
            scene_id=r.scene_id,
            scene_index=r.scene_index,
            start_sec=start,
            end_sec=end,
            duration_sec=max(0.0, end - start),
            text=r.text,
            concept=r.concept,
            narrative_function=r.narrative_function,
            selected_clip_id=r.selected_clip_id,
        )


class PlaybackSessionService:
    def __init__(
        self,
        *,
        timeline: PlaybackTimelineReadPort,
        media: PlaybackMediaPort,
        waveform: WaveformPort,
    ) -> None:
        self._timeline = timeline
        self._media = media
        self._waveform = waveform

    def build_session(self, session: Any, project_id: str, project_name: str) -> PlaybackSessionBundle:
        scenes = self._timeline.load_scenes(session, project_id)
        duration_sec = max((s.end_sec for s in scenes), default=0.0)
        audio_path = self._media.resolve_project_audio(session, project_id)
        wf: WaveformPeaks | None = None
        if audio_path is not None:
            try:
                wf = self._waveform.extract(audio_path)
                duration_sec = max(duration_sec, wf.duration_sec)
            except Exception:
                wf = None
        return PlaybackSessionBundle(
            project_id=project_id,
            project_name=project_name,
            duration_sec=duration_sec,
            scenes=scenes,
            waveform=wf,
            has_project_audio=audio_path is not None,
            has_waveform=wf is not None,
        )
