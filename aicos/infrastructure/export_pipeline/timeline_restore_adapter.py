"""Restaura timeline desde snapshot usando el repositorio cinematic_timeline."""

from __future__ import annotations

from aicos.domain.cinematic_timeline.entities import ProjectTimelineScene
from aicos.domain.export_pipeline.entities import ExportTimelineScene
from aicos.infrastructure.cinematic_timeline.sql_project_timeline_repository import SqlProjectTimelineRepository


class TimelineRestoreAdapter:
    def __init__(self) -> None:
        self._repo = SqlProjectTimelineRepository()

    def replace_timeline_from_bundle(
        self, session, project_id: str, scenes: tuple[ExportTimelineScene, ...]
    ) -> tuple[ProjectTimelineScene, ...]:
        ordered = sorted(scenes, key=lambda s: s.scene_index)
        entities = [
            ProjectTimelineScene(
                scene_id=s.scene_id,
                scene_index=s.scene_index,
                start_ms=s.start_ms,
                end_ms=s.end_ms,
                duration_ms=s.duration_ms,
                text=s.text,
                concept=s.concept,
                narrative_function=s.narrative_function,
                is_hook=s.is_hook,
                gender_hint=None,
                selected_clip_id=s.selected_clip_id,
            )
            for s in ordered
        ]
        self._repo.replace_timeline(session, project_id, tuple(entities))
        return tuple(entities)
