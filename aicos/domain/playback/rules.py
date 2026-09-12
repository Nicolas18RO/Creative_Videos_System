"""Reglas de sincronización temporal y máquina de estados de playback."""

from __future__ import annotations

from aicos.domain.playback.entities import PlaybackCue, PlaybackSceneMap, PlaybackState

_ALLOWED: dict[PlaybackState, frozenset[PlaybackState]] = {
    PlaybackState.IDLE: frozenset({PlaybackState.LOADING, PlaybackState.READY, PlaybackState.ERROR}),
    PlaybackState.LOADING: frozenset({PlaybackState.READY, PlaybackState.ERROR, PlaybackState.IDLE}),
    PlaybackState.READY: frozenset(
        {PlaybackState.PLAYING, PlaybackState.PAUSED, PlaybackState.SEEKING, PlaybackState.SCENE_LOOP, PlaybackState.LOADING}
    ),
    PlaybackState.PLAYING: frozenset(
        {PlaybackState.PAUSED, PlaybackState.SEEKING, PlaybackState.READY, PlaybackState.SCENE_LOOP, PlaybackState.ERROR}
    ),
    PlaybackState.PAUSED: frozenset(
        {PlaybackState.PLAYING, PlaybackState.SEEKING, PlaybackState.READY, PlaybackState.SCENE_LOOP, PlaybackState.ERROR}
    ),
    PlaybackState.SEEKING: frozenset({PlaybackState.PLAYING, PlaybackState.PAUSED, PlaybackState.READY, PlaybackState.SCENE_LOOP}),
    PlaybackState.SCENE_LOOP: frozenset({PlaybackState.PLAYING, PlaybackState.PAUSED, PlaybackState.READY, PlaybackState.SEEKING}),
    PlaybackState.ERROR: frozenset({PlaybackState.IDLE, PlaybackState.LOADING}),
}


def can_transition(current: PlaybackState, target: PlaybackState) -> bool:
    if current == target:
        return True
    return target in _ALLOWED.get(current, frozenset())


def clamp_time(time_sec: float, *, duration_sec: float) -> float:
    if duration_sec <= 0:
        return 0.0
    return max(0.0, min(float(time_sec), duration_sec))


def active_scene_at_time(
    scenes: tuple[PlaybackSceneMap, ...],
    time_sec: float,
) -> PlaybackSceneMap | None:
    """Escena narrativa activa según tiempo global del guion."""
    t = float(time_sec)
    for s in scenes:
        if s.start_sec <= t < s.end_sec - 1e-6:
            return s
    if scenes and t >= scenes[-1].end_sec - 1e-6:
        return scenes[-1]
    return scenes[0] if scenes else None


def scene_local_time(scene: PlaybackSceneMap, global_time_sec: float) -> float:
    return clamp_time(global_time_sec - scene.start_sec, duration_sec=scene.duration_sec)


def build_cue(scene: PlaybackSceneMap | None) -> PlaybackCue | None:
    if scene is None:
        return None
    return PlaybackCue(
        scene_id=scene.scene_id,
        scene_index=scene.scene_index,
        text=scene.text,
        start_sec=scene.start_sec,
        end_sec=scene.end_sec,
    )
