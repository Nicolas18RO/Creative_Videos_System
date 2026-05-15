"""Detección de hook de apertura (señales puras sobre TimelineScene)."""

from __future__ import annotations

import statistics

from aicos.domain.editorial_dataset.entities import HookDetectionResult, TimelineScene


def detect_opening_hook(
    scenes: tuple[TimelineScene, ...],
    *,
    min_hook_duration: float,
    max_hook_duration: float,
) -> tuple[HookDetectionResult, ...]:
    if not scenes:
        return ()
    t_max = float(max_hook_duration)
    t_min = float(min_hook_duration)
    reasons: list[str] = []
    window_scenes = [s for s in scenes if s.start_time < t_max]
    if not window_scenes:
        return ()

    durs = [s.duration for s in window_scenes]
    mean_dur = statistics.fmean(durs) if durs else 0.0
    cut_density = len(window_scenes) / max(t_max, 1e-6)
    motion = statistics.fmean(s.motion_intensity for s in window_scenes)
    energy = statistics.fmean(s.visual_energy for s in window_scenes)
    trans_hits = sum(
        1
        for s in window_scenes
        if (s.transition_type or "").lower() not in ("", "cut", "none", "hard_cut")
    )

    def _clamp01(x: float) -> float:
        return max(0.0, min(1.0, x))

    if mean_dur > 0 and mean_dur < t_min * 1.2:
        reasons.append("fast_cuts_in_opening")
    if cut_density > 0.35:
        reasons.append("high_cut_rate")
    if motion > 0.55:
        reasons.append("motion_spike")
    if energy > 0.55:
        reasons.append("high_visual_energy")
    if trans_hits >= 1:
        reasons.append("non_default_transitions")

    ultra = [s for s in window_scenes if s.start_time < min(2.0, t_max)]
    opening_boost = 0.0
    if ultra:
        opening_boost = _clamp01(
            statistics.fmean(s.motion_intensity + s.visual_energy for s in ultra) / 2.0
        )

    strength = _clamp01(
        0.22 * _clamp01(cut_density / 0.5)
        + 0.22 * _clamp01(1.0 - min(1.0, mean_dur / max(t_max * 0.5, 1e-6)))
        + 0.18 * _clamp01(motion)
        + 0.18 * _clamp01(energy)
        + 0.12 * _clamp01(trans_hits / 3.0)
        + 0.08 * opening_boost
    )
    if not reasons:
        reasons.append("baseline_opening_energy")
    end_t = min(t_max, max(s.end_time for s in window_scenes))
    return (
        HookDetectionResult(
            window_start=0.0,
            window_end=float(end_t),
            hook_strength=strength,
            reasons=tuple(reasons),
        ),
    )
