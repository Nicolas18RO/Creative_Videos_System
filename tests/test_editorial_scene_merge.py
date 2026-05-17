"""Tests fusión pura de escenas."""

from __future__ import annotations

from aicos.domain.editorial_dataset.entities import TimelineScene
from aicos.domain.editorial_review.rules import merge_requires_adjacent_scenes
from aicos.domain.editorial_review.scene_merge import merge_timeline_scenes


def _sc(idx: int, start: float, end: float, role: str = "BENEFIT") -> TimelineScene:
    return TimelineScene(
        scene_index=idx,
        clip_id=f"c{idx}",
        start_time=start,
        end_time=end,
        duration=end - start,
        transition_type="cut",
        narrative_role=role,
        motion_intensity=0.5,
        visual_energy=0.5,
        camera_type="",
        semantic_tags=("a",),
        emotion_tags=(),
    )


def test_merge_union_duration_and_hook_role() -> None:
    a = _sc(0, 0, 2, "HOOK")
    b = _sc(1, 2, 5, "BENEFIT")
    m = merge_timeline_scenes(a, b, resulting_scene_index=0)
    assert m.start_time == 0
    assert m.end_time == 5
    assert abs(m.duration - 5) < 1e-6
    assert m.narrative_role == "HOOK"
    assert "a" in m.semantic_tags


def test_adjacent_rule() -> None:
    assert merge_requires_adjacent_scenes(0, 1)
    assert not merge_requires_adjacent_scenes(0, 2)
