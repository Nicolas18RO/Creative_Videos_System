"""Tests dominio pacing timeline visual (Fase 6.8)."""

from __future__ import annotations

from aicos.domain.editorial_dataset.entities import TimelineScene
from aicos.domain.timeline_visualization.pacing import (
    build_motion_curve,
    build_pacing_density,
    hook_probability_for_scene,
    scene_cut_speed,
    timeline_position_for_scene,
)


def _scene(idx: int, start: float, end: float, role: str = "BENEFIT", motion: float = 0.5, energy: float = 0.4) -> TimelineScene:
    return TimelineScene(
        scene_index=idx,
        clip_id=f"c{idx}",
        start_time=start,
        end_time=end,
        duration=end - start,
        transition_type="cut",
        narrative_role=role,
        motion_intensity=motion,
        visual_energy=energy,
        camera_type="",
        semantic_tags=(),
        emotion_tags=(),
    )


def test_pacing_density_faster_cuts_score_higher() -> None:
    fast = _scene(0, 0, 0.5)
    slow = _scene(1, 1, 4.0)
    dens = build_pacing_density((fast, slow))
    assert dens[0] >= dens[1]


def test_hook_probability_boost_for_hook_role() -> None:
    hook = _scene(0, 0, 2, role="HOOK", energy=0.5, motion=0.5)
    plain = _scene(1, 2, 4, role="BENEFIT", energy=0.5, motion=0.5)
    assert hook_probability_for_scene(hook) > hook_probability_for_scene(plain)


def test_timeline_position_midpoint() -> None:
    s = _scene(0, 2, 4)
    assert abs(timeline_position_for_scene(s, 10.0) - 0.3) < 1e-6


def test_motion_curve_normalized() -> None:
    scenes = (_scene(0, 0, 1, motion=1.2), _scene(1, 1, 2, motion=-0.1))
    curve = build_motion_curve(scenes)
    assert curve[0] == 1.0
    assert curve[1] == 0.0


def test_scene_cut_speed_inverse_duration() -> None:
    assert scene_cut_speed(_scene(0, 0, 0.25)) > scene_cut_speed(_scene(1, 0, 2.0))
