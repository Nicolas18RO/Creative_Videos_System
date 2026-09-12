"""Mapeo dominio → contratos API."""

from __future__ import annotations

from aicos.domain.cinematic_timeline.entities import ProjectTimelineScene
from aicos.models.schemas import ProjectTimelineSceneOut, ProjectTimelineSnapshotOut


def scene_to_out(s: ProjectTimelineScene) -> ProjectTimelineSceneOut:
    return ProjectTimelineSceneOut(
        scene_id=s.scene_id,
        scene_index=s.scene_index,
        start_ms=s.start_ms,
        end_ms=s.end_ms,
        duration_ms=s.duration_ms,
        start_sec=s.start_sec,
        end_sec=s.end_sec,
        text=s.text,
        concept=s.concept,
        narrative_function=s.narrative_function,
        is_hook=s.is_hook,
        gender_hint=s.gender_hint,
        selected_clip_id=s.selected_clip_id,
    )


def snapshot_to_out(
    scenes: tuple[ProjectTimelineScene, ...],
    *,
    project_id: str,
    timeline_duration_ms: int,
) -> ProjectTimelineSnapshotOut:
    return ProjectTimelineSnapshotOut(
        project_id=project_id,
        timeline_duration_ms=timeline_duration_ms,
        timeline_duration_sec=timeline_duration_ms / 1000.0,
        scenes=[scene_to_out(s) for s in scenes],
    )
