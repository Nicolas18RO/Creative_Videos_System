"""Codificación estructural determinista → vector fijo (representación de estilo)."""

from __future__ import annotations

import hashlib
import math

from aicos.domain.editorial_style_embedding.entities import StyleStructuralSource

_STRUCTURAL_DIM = 128
_TAG_BUCKETS = 40


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def _norm(x: float, hi: float) -> float:
    return _clamp01(x / hi) if hi > 0 else 0.0


def _tag_bucket_activation(tags: tuple[str, ...], extra: tuple[str, ...], dim: int = _TAG_BUCKETS) -> list[float]:
    vec = [0.0] * dim
    for t in list(tags) + list(extra):
        if not t:
            continue
        h = int(hashlib.sha1(t.encode("utf-8")).hexdigest(), 16) % dim
        vec[h] = min(1.0, vec[h] + 0.35)
    return vec


def structural_vector_from_source(src: StyleStructuralSource) -> tuple[float, ...]:
    """128 floats: escalares normalizados + activación dispersa de etiquetas/patrones."""
    scalars: list[float] = [
        _norm(float(src.scene_count), 40.0),
        _norm(src.total_duration_sec, 120.0),
        _clamp01(src.hook_intensity),
        _clamp01(src.average_pacing / 10.0),
        _clamp01(src.motion_density),
        _clamp01(src.transition_density),
        _clamp01(src.narrative_aggressiveness),
        _clamp01(src.visual_dynamism),
        _clamp01(src.pacing_score),
        _clamp01(src.hook_strength_signal),
        _clamp01(src.emotional_curve_mean),
        _clamp01(src.emotional_curve_std),
        _norm(src.cut_mean_shot_sec, 8.0),
        _norm(src.cut_std_shot_sec, 5.0),
        _clamp01(src.cut_cv),
        _norm(src.cuts_per_minute, 80.0),
        _clamp01((src.cut_accel + 1.0) / 2.0),
        _norm(float(src.burst_window_count), 12.0),
        _clamp01(src.momentum_mean),
        _clamp01(src.momentum_variance),
        _clamp01(src.momentum_reversals_norm),
        _clamp01(src.sustained_high_blocks_norm),
        _clamp01(src.narrative_phase_confidence),
        _clamp01(src.narrative_structure_bucket / 4.0),
        _clamp01(src.usage_source_entropy),
        _clamp01(src.usage_max_cluster_streak_norm),
        _clamp01(src.usage_pressure_mean_norm),
    ]
    while len(scalars) < 88:
        scalars.append(0.0)
    scalars = scalars[:88]

    tag_part = _tag_bucket_activation(
        src.signature_tags + src.cinematic_overlay_tags,
        src.top_pattern_tokens,
        dim=_TAG_BUCKETS,
    )
    out = scalars + tag_part
    if len(out) != _STRUCTURAL_DIM:
        raise RuntimeError("structural_dim_mismatch")
    # L2 normalize para similitud coseno estable
    norm = math.sqrt(sum(x * x for x in out)) or 1.0
    return tuple(float(x / norm) for x in out)
