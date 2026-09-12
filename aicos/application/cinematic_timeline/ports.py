"""Puertos del timeline de proyecto."""

from __future__ import annotations

from typing import Any, Protocol

from aicos.domain.cinematic_timeline.entities import ProjectTimelineScene


class ProjectTimelinePersistencePort(Protocol):
    def load_timeline(self, session: Any, project_id: str) -> tuple[ProjectTimelineScene, ...]: ...

    def project_duration_ms(self, session: Any, project_id: str) -> int: ...

    def replace_timeline(
        self,
        session: Any,
        project_id: str,
        scenes: tuple[ProjectTimelineScene, ...],
        *,
        deleted_scene_ids: tuple[str, ...] = (),
    ) -> None: ...
