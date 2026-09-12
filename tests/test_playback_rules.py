"""Reglas de dominio playback."""

from aicos.domain.playback.entities import PlaybackSceneMap, PlaybackState
from aicos.domain.playback.rules import (
    active_scene_at_time,
    can_transition,
    clamp_time,
    scene_local_time,
)


def _map(idx: int, start: float, end: float) -> PlaybackSceneMap:
    return PlaybackSceneMap(
        scene_id=f"s{idx}",
        scene_index=idx,
        start_sec=start,
        end_sec=end,
        duration_sec=end - start,
        text=f"line {idx}",
        concept="",
        narrative_function="PROBLEM",
        selected_clip_id=None,
    )


def test_state_transitions() -> None:
    assert can_transition(PlaybackState.IDLE, PlaybackState.LOADING)
    assert not can_transition(PlaybackState.IDLE, PlaybackState.PLAYING)


def test_active_scene_at_time() -> None:
    scenes = (_map(0, 0, 2), _map(1, 2, 5))
    s = active_scene_at_time(scenes, 2.5)
    assert s is not None
    assert s.scene_index == 1


def test_clamp_and_local() -> None:
    sc = _map(0, 1.0, 4.0)
    assert clamp_time(10, duration_sec=3) == 3
    assert scene_local_time(sc, 2.0) == 1.0
