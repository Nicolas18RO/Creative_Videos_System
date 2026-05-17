"""Tests dominio Fase 6.8 — vista previa de fusión."""

from aicos.domain.editorial_dataset.entities import TimelineScene
from aicos.domain.editorial_training.merge_preview import build_merge_preview


def _scene(idx: int, start: float, end: float) -> TimelineScene:
    return TimelineScene(
        scene_index=idx,
        clip_id=f"c{idx}",
        start_time=start,
        end_time=end,
        duration=end - start,
        transition_type="cut",
        narrative_role="HOOK" if idx == 0 else "NATURAL",
        motion_intensity=0.5,
        visual_energy=0.5,
        camera_type="",
        semantic_tags=("a",),
        emotion_tags=(),
    )


def test_merge_preview_union_duration():
    left = _scene(12, 12.1, 14.5)
    right = _scene(13, 14.5, 16.2)
    preview = build_merge_preview(left, right)
    assert preview.merged.start_time == 12.1
    assert preview.merged.end_time == 16.2
    assert abs(preview.total_duration - 4.1) < 0.01
    assert preview.removed_boundary_time == 14.5
