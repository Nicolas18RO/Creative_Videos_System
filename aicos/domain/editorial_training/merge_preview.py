"""Vista previa pura de fusión de escenas (Fase 6.8)."""

from __future__ import annotations

from dataclasses import dataclass

from aicos.domain.editorial_dataset.entities import TimelineScene
from aicos.domain.editorial_review.scene_merge import merge_timeline_scenes


@dataclass(frozen=True, slots=True)
class MergePreviewSceneSlice:
    scene_index: int
    start_time: float
    end_time: float
    duration: float
    clip_id: str
    narrative_role: str


@dataclass(frozen=True, slots=True)
class MergePreviewResult:
    scene_a: MergePreviewSceneSlice
    scene_b: MergePreviewSceneSlice
    merged: MergePreviewSceneSlice
    removed_boundary_time: float
    total_duration: float


def _slice_from_scene(scene: TimelineScene) -> MergePreviewSceneSlice:
    return MergePreviewSceneSlice(
        scene_index=scene.scene_index,
        start_time=round(scene.start_time, 3),
        end_time=round(scene.end_time, 3),
        duration=round(scene.duration, 3),
        clip_id=scene.clip_id,
        narrative_role=scene.narrative_role,
    )


def build_merge_preview(left: TimelineScene, right: TimelineScene) -> MergePreviewResult:
    """Calcula resultado de fusión sin persistir."""
    merged_scene = merge_timeline_scenes(left, right, resulting_scene_index=left.scene_index)
    boundary = round(max(left.end_time, right.start_time), 3)
    if abs(left.end_time - right.start_time) < 1e-6:
        boundary = round(left.end_time, 3)
    return MergePreviewResult(
        scene_a=_slice_from_scene(left),
        scene_b=_slice_from_scene(right),
        merged=_slice_from_scene(merged_scene),
        removed_boundary_time=boundary,
        total_duration=round(merged_scene.duration, 3),
    )
