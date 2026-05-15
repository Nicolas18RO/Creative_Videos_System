"""Entidades puras del embedding de estilo editorial."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StyleStructuralSource:
    """Señales ya agregadas (sin ORM) para codificar un vector estructural fijo."""

    creative_id: str
    scene_count: int
    total_duration_sec: float
    # Perfil 6.1
    hook_intensity: float
    average_pacing: float
    motion_density: float
    transition_density: float
    narrative_aggressiveness: float
    visual_dynamism: float
    pacing_score: float
    hook_strength_signal: float
    emotional_curve_mean: float
    emotional_curve_std: float
    # Ritmo / momentum / narrativa (6.2 o derivado de timeline)
    cut_mean_shot_sec: float
    cut_std_shot_sec: float
    cut_cv: float
    cuts_per_minute: float
    cut_accel: float
    burst_window_count: int
    momentum_mean: float
    momentum_variance: float
    momentum_reversals_norm: float
    sustained_high_blocks_norm: float
    narrative_phase_confidence: float
    narrative_structure_bucket: int
    usage_source_entropy: float
    usage_max_cluster_streak_norm: float
    usage_pressure_mean_norm: float
    # Secuencias compactas (tokens ya resumidos)
    signature_tags: tuple[str, ...]
    cinematic_overlay_tags: tuple[str, ...]
    top_pattern_tokens: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class EditorialStyleEmbedding:
    """Representación vectorial reutilizable del estilo editorial de un creativo."""

    creative_id: str
    structural_vector: tuple[float, ...]
    semantic_vector: tuple[float, ...] | None
    fused_vector: tuple[float, ...]
    digest_text: str
    digest_sha256: str
    structural_model_tag: str
    semantic_model_tag: str | None
    fusion_mode: str
