"""Curvas de pacing y densidad visual (lógica pura, sin FFmpeg)."""

from __future__ import annotations

from aicos.domain.editorial_dataset.entities import TimelineScene


def scene_cut_speed(scene: TimelineScene) -> float:
    """Cortes por segundo inversamente proporcionales a la duración."""
    d = max(scene.duration, 0.05)
    return min(4.0, 1.0 / d)


def build_motion_curve(scenes: tuple[TimelineScene, ...]) -> tuple[float, ...]:
    if not scenes:
        return ()
    return tuple(max(0.0, min(1.0, s.motion_intensity)) for s in scenes)


def build_pacing_density(scenes: tuple[TimelineScene, ...]) -> tuple[float, ...]:
    """Densidad de cortes normalizada por escena (cortes rápidos → valor alto)."""
    if not scenes:
        return ()
    speeds = [scene_cut_speed(s) for s in scenes]
    mx = max(speeds) or 1.0
    return tuple(min(1.0, v / mx) for v in speeds)


def build_transition_density(scenes: tuple[TimelineScene, ...]) -> tuple[float, ...]:
    """Heurística: transiciones no-cut aumentan densidad de cambio visual."""
    if not scenes:
        return ()
    out: list[float] = []
    for s in scenes:
        tt = (s.transition_type or "cut").strip().lower()
        boost = 0.35 if tt not in ("cut", "") else 0.0
        out.append(min(1.0, s.visual_energy * 0.65 + boost))
    return tuple(out)


def hook_probability_for_scene(scene: TimelineScene) -> float:
    nr = (scene.narrative_role or "").strip().upper()
    base = scene.visual_energy * 0.4 + scene.motion_intensity * 0.35
    if nr == "HOOK":
        return min(1.0, base + 0.45)
    return min(1.0, base)


def timeline_position_for_scene(scene: TimelineScene, total_duration: float) -> float:
    if total_duration <= 0:
        return 0.0
    mid = (scene.start_time + scene.end_time) * 0.5
    return max(0.0, min(1.0, mid / total_duration))
