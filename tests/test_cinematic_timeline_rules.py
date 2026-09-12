"""Reglas puras del timeline de proyecto."""

from aicos.domain.cinematic_timeline.entities import ProjectTimelineScene
from aicos.domain.cinematic_timeline.rules import (
    merge_project_scenes,
    reorder_scenes,
    split_project_scene,
    trim_project_scene,
    validate_project_timeline,
)


def _scene(idx: int, start: int, end: int, sid: str | None = None) -> ProjectTimelineScene:
    return ProjectTimelineScene(
        scene_id=sid or f"s{idx}",
        scene_index=idx,
        start_ms=start,
        end_ms=end,
        duration_ms=end - start,
        text=f"text {idx}",
        concept=f"concept {idx}",
        narrative_function="PROBLEM",
        is_hook=False,
        gender_hint=None,
        selected_clip_id=None,
    )


def test_merge_adjacent_scenes() -> None:
    a = _scene(0, 0, 2000)
    b = _scene(1, 2000, 5000)
    m = merge_project_scenes(a, b)
    assert m.start_ms == 0
    assert m.end_ms == 5000
    assert m.duration_ms == 5000


def test_split_scene() -> None:
    s = _scene(0, 0, 4000)
    left, right = split_project_scene(s, 1500)
    assert left.end_ms == 1500
    assert right.start_ms == 1500
    assert right.scene_id != s.scene_id


def test_reorder_scenes() -> None:
    scenes = [_scene(0, 0, 1000), _scene(1, 1000, 2000), _scene(2, 2000, 3000)]
    out = reorder_scenes(scenes, 2, 0)
    assert [s.scene_index for s in out] == [0, 1, 2]
    assert out[0].scene_id == "s2"


def test_trim_scene() -> None:
    s = _scene(0, 0, 5000)
    t = trim_project_scene(s, start_ms=500, end_ms=4500)
    assert t.start_ms == 500
    assert t.end_ms == 4500


def test_validate_no_overlap() -> None:
    ok, _ = validate_project_timeline((_scene(0, 0, 2000), _scene(1, 2000, 4000)))
    assert ok
