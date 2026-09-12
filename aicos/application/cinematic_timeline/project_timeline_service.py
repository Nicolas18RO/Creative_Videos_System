"""Orquestación de mutaciones del timeline de proyecto."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aicos.application.cinematic_timeline.ports import ProjectTimelinePersistencePort
from aicos.domain.cinematic_timeline.entities import ProjectTimelineScene
from aicos.domain.cinematic_timeline.rules import (
    merge_project_scenes,
    reorder_scenes,
    split_project_scene,
    trim_project_scene,
    validate_project_timeline,
)
from aicos.domain.editorial_review.rules import scenes_adjacent_in_ordered_list


@dataclass(frozen=True, slots=True)
class TimelineMutationResult:
    scenes: tuple[ProjectTimelineScene, ...]
    timeline_duration_ms: int


class ProjectTimelineService:
    def __init__(self, *, persistence: ProjectTimelinePersistencePort) -> None:
        self._persistence = persistence

    def get_snapshot(self, session: Any, project_id: str) -> TimelineMutationResult:
        scenes = self._persistence.load_timeline(session, project_id)
        dur = self._persistence.project_duration_ms(session, project_id)
        return TimelineMutationResult(scenes=scenes, timeline_duration_ms=dur)

    def _persist(
        self,
        session: Any,
        project_id: str,
        scenes: list[ProjectTimelineScene],
        *,
        deleted: tuple[str, ...] = (),
    ) -> TimelineMutationResult:
        ordered = sorted(scenes, key=lambda s: s.scene_index)
        ok, msg = validate_project_timeline(
            tuple(ordered),
            timeline_duration_ms=max((s.end_ms for s in ordered), default=0),
        )
        if not ok:
            raise ValueError(msg)
        self._persistence.replace_timeline(session, project_id, tuple(ordered), deleted_scene_ids=deleted)
        dur = max((s.end_ms for s in ordered), default=0)
        return TimelineMutationResult(scenes=tuple(ordered), timeline_duration_ms=dur)

    def reorder(
        self,
        session: Any,
        project_id: str,
        *,
        from_index: int,
        to_index: int,
    ) -> TimelineMutationResult:
        scenes = list(self._persistence.load_timeline(session, project_id))
        next_scenes = reorder_scenes(scenes, from_index, to_index)
        return self._persist(session, project_id, next_scenes)

    def merge(
        self,
        session: Any,
        project_id: str,
        *,
        scene_index_a: int,
        scene_index_b: int,
    ) -> TimelineMutationResult:
        scenes = list(self._persistence.load_timeline(session, project_id))
        by_idx = {s.scene_index: s for s in scenes}
        left = by_idx.get(scene_index_a)
        right = by_idx.get(scene_index_b)
        if left is None or right is None:
            raise ValueError("scene_not_found")
        active = sorted(scenes, key=lambda s: s.start_ms)
        indices = tuple(s.scene_index for s in active)
        if not scenes_adjacent_in_ordered_list(indices, scene_index_a, scene_index_b):
            raise ValueError("scenes_not_adjacent")
        merged = merge_project_scenes(left, right)
        deleted_id = right.scene_id
        remaining = [s for s in scenes if s.scene_id not in (left.scene_id, right.scene_id)]
        remaining.append(merged)
        from aicos.domain.cinematic_timeline.rules import _reindex_chronological

        reindexed = _reindex_chronological(remaining)
        return self._persist(session, project_id, reindexed, deleted=(deleted_id,))

    def split(
        self,
        session: Any,
        project_id: str,
        *,
        scene_id: str,
        split_at_ms: int,
    ) -> TimelineMutationResult:
        scenes = list(self._persistence.load_timeline(session, project_id))
        target = next((s for s in scenes if s.scene_id == scene_id), None)
        if target is None:
            raise ValueError("scene_not_found")
        left, right = split_project_scene(target, split_at_ms)
        rest = [s for s in scenes if s.scene_id != scene_id]
        rest.extend([left, right])
        from aicos.domain.cinematic_timeline.rules import _reindex_chronological

        return self._persist(session, project_id, _reindex_chronological(rest))

    def trim(
        self,
        session: Any,
        project_id: str,
        *,
        scene_id: str,
        start_ms: int,
        end_ms: int,
    ) -> TimelineMutationResult:
        scenes = list(self._persistence.load_timeline(session, project_id))
        out: list[ProjectTimelineScene] = []
        for s in scenes:
            if s.scene_id == scene_id:
                out.append(trim_project_scene(s, start_ms=start_ms, end_ms=end_ms))
            else:
                out.append(s)
        return self._persist(session, project_id, out)

    def replace_clip(
        self,
        session: Any,
        project_id: str,
        *,
        scene_id: str,
        clip_id: str,
    ) -> TimelineMutationResult:
        scenes = list(self._persistence.load_timeline(session, project_id))
        out: list[ProjectTimelineScene] = []
        found = False
        for s in scenes:
            if s.scene_id == scene_id:
                found = True
                out.append(
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
                        gender_hint=s.gender_hint,
                        selected_clip_id=clip_id,
                    )
                )
            else:
                out.append(s)
        if not found:
            raise ValueError("scene_not_found")
        return self._persist(session, project_id, out)
