"""Análisis de ritmo de corte y ráfagas (dominio puro)."""

from __future__ import annotations

import statistics

from aicos.domain.editorial_pattern_engine.entities import CutBurstWindow, CutRhythmProfile


def analyze_cut_rhythm(
    scene_start_times: tuple[float, ...],
    scene_durations: tuple[float, ...],
) -> CutRhythmProfile:
    if not scene_durations:
        return CutRhythmProfile(
            mean_shot_duration=0.0,
            std_shot_duration=0.0,
            coefficient_of_variation=0.0,
            cuts_per_minute=0.0,
            acceleration_index=0.0,
            burst_windows=(),
        )
    mean_d = statistics.fmean(scene_durations)
    std_d = statistics.pstdev(scene_durations) if len(scene_durations) > 1 else 0.0
    cv = (std_d / mean_d) if mean_d > 1e-9 else 0.0
    t_end = scene_start_times[-1] + scene_durations[-1] if scene_start_times else 0.0
    minutes = max(t_end / 60.0, 1e-6)
    cpm = len(scene_durations) / minutes

    # Aceleración: contraste entre mitades (cortes por minuto 2º vs 1º mitad).
    mid_t = t_end * 0.5
    first = [scene_durations[i] for i in range(len(scene_durations)) if scene_start_times[i] < mid_t]
    second = [scene_durations[i] for i in range(len(scene_durations)) if scene_start_times[i] >= mid_t]
    cpm1 = len(first) / max(mid_t / 60.0, 1e-6) if first else cpm
    cpm2 = len(second) / max((t_end - mid_t) / 60.0, 1e-6) if second else cpm
    accel = max(-1.0, min(1.0, (cpm2 - cpm1) / max(cpm1, 1e-6)))

    # Ventana deslizante ~2.5s: densidad local de cortes vs global.
    burst_windows: list[CutBurstWindow] = []
    window = 2.5
    global_density = len(scene_durations) / max(t_end, 1e-6)
    i = 0
    while i < len(scene_start_times):
        w0 = scene_start_times[i]
        w1 = w0 + window
        idxs = [j for j in range(len(scene_start_times)) if w0 <= scene_start_times[j] < w1]
        if not idxs:
            i += 1
            continue
        local_density = len(idxs) / max(window, 1e-6)
        intensity = max(0.0, min(2.5, (local_density / max(global_density, 1e-6)) - 1.0))
        if intensity > 0.25:
            burst_windows.append(
                CutBurstWindow(
                    window_start=w0,
                    window_end=min(w1, t_end),
                    burst_intensity=float(intensity),
                    shots_in_window=len(idxs),
                )
            )
        i += max(1, len(idxs) // 2)
    return CutRhythmProfile(
        mean_shot_duration=float(mean_d),
        std_shot_duration=float(std_d),
        coefficient_of_variation=float(cv),
        cuts_per_minute=float(cpm),
        acceleration_index=float(accel),
        burst_windows=tuple(burst_windows[:12]),
    )
