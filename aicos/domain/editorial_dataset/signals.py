"""Derivación determinista de señales editoriales a partir de escenas (dominio puro)."""

from __future__ import annotations

import math
import statistics

from aicos.domain.editorial_dataset.entities import CreativeStyleProfile, EditorialStyleSignals, TimelineScene

_EMOTION_WEIGHTS: dict[str, float] = {
    "tension": 0.85,
    "euphoria": 0.95,
    "calm": 0.25,
    "neutral": 0.45,
    "aggressive": 0.9,
    "curiosity": 0.65,
    "fear": 0.8,
    "joy": 0.75,
}


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def _emotion_scalar(tags: tuple[str, ...]) -> float:
    if not tags:
        return 0.5
    vals = [_EMOTION_WEIGHTS.get(t.lower(), 0.55) for t in tags]
    return float(sum(vals) / len(vals))


def compute_emotional_curve(scenes: tuple[TimelineScene, ...]) -> tuple[float, ...]:
    out: list[float] = []
    for s in scenes:
        base = 0.55 * _clamp01(s.visual_energy) + 0.45 * _clamp01(s.motion_intensity)
        emo = _emotion_scalar(s.emotion_tags)
        out.append(_clamp01(0.5 * base + 0.5 * emo))
    return tuple(out)


def compute_pacing_score(scenes: tuple[TimelineScene, ...], total_duration: float) -> float:
    if not scenes or total_duration <= 0:
        return 0.0
    mean_dur = statistics.fmean(s.duration for s in scenes)
    cut_rate = len(scenes) / total_duration
    # Cortes frecuentes + duraciones cortas → pacing alto.
    dur_term = _clamp01(1.0 - min(1.0, mean_dur / max(total_duration * 0.25, 1e-6)))
    rate_term = _clamp01(cut_rate / 2.0)
    return _clamp01(0.55 * rate_term + 0.45 * dur_term)


def compute_motion_density(scenes: tuple[TimelineScene, ...]) -> float:
    if not scenes:
        return 0.0
    return _clamp01(statistics.fmean(s.motion_intensity for s in scenes))


def compute_transition_density(scenes: tuple[TimelineScene, ...], total_duration: float) -> float:
    if total_duration <= 0:
        return 0.0
    non_hard = sum(1 for s in scenes if (s.transition_type or "").strip().lower() not in ("", "cut", "none"))
    return _clamp01(non_hard / max(total_duration / 3.0, 1e-6))


def compute_narrative_aggressiveness(scenes: tuple[TimelineScene, ...]) -> float:
    if not scenes:
        return 0.0
    roles = [((s.narrative_role or "").lower()) for s in scenes]
    aggressive_tokens = ("hook", "punch", "reveal", "cta", "shock", "impact")
    hits = sum(1 for r in roles if any(tok in r for tok in aggressive_tokens))
    return _clamp01(hits / len(scenes) + 0.35 * compute_motion_density(scenes))


def compute_visual_dynamism(scenes: tuple[TimelineScene, ...]) -> float:
    if not scenes:
        return 0.0
    energies = [s.visual_energy for s in scenes]
    mean_e = statistics.fmean(energies)
    if len(energies) < 2:
        var = 0.0
    else:
        var = statistics.pvariance(energies)
    var_term = _clamp01(math.sqrt(var) * 2.0)
    return _clamp01(0.65 * _clamp01(mean_e) + 0.35 * var_term)


def compute_average_pacing(scenes: tuple[TimelineScene, ...], total_duration: float) -> float:
    """Duración media de plano (segundos); timeline más 'lento' si planos largos."""
    if not scenes or total_duration <= 0:
        return 0.0
    return float(statistics.fmean(s.duration for s in scenes))


def build_style_profile_and_signals(
    scenes: tuple[TimelineScene, ...],
    *,
    hook_strength: float,
    cinematic_style_tags: tuple[str, ...],
) -> tuple[CreativeStyleProfile, EditorialStyleSignals]:
    total_dur = max(s.end_time for s in scenes) if scenes else 0.0
    motion = compute_motion_density(scenes)
    trans = compute_transition_density(scenes, total_dur)
    narrative = compute_narrative_aggressiveness(scenes)
    dyn = compute_visual_dynamism(scenes)
    avg_pace = compute_average_pacing(scenes, total_dur)
    pacing_score = compute_pacing_score(scenes, total_dur)
    curve = compute_emotional_curve(scenes)
    hook_intensity = _clamp01(0.5 * hook_strength + 0.5 * min(1.0, pacing_score * 1.15))
    profile = CreativeStyleProfile(
        hook_intensity=hook_intensity,
        average_pacing=avg_pace,
        motion_density=motion,
        transition_density=trans,
        narrative_aggressiveness=narrative,
        visual_dynamism=dyn,
        cinematic_style_tags=cinematic_style_tags,
    )
    signals = EditorialStyleSignals(
        pacing_score=pacing_score,
        hook_strength=_clamp01(hook_strength),
        emotional_curve=curve,
        visual_dynamism=dyn,
    )
    return profile, signals
