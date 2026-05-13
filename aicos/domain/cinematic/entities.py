"""Entidades de dominio: metadata de clip, emoción, narrativa e intención visual."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from aicos.domain.cinematic.enums import (
    CameraMovement,
    CameraType,
    CinematicStyle,
    ColorMood,
    EmotionType,
    EnergyLevel,
    EnvironmentType,
    Framing,
    LightingStyle,
    MarketingUsage,
    NarrativeRole,
    Pacing,
    TransitionCompatibility,
    VisualIntentKind,
)


@dataclass(frozen=True, slots=True)
class NarrativeClassificationResult:
    """Salida del motor de clasificación narrativa."""

    narrative_role: NarrativeRole
    confidence: float
    reasoning: str
    compatible_visual_styles: tuple[str, ...] = ()
    pacing_recommendation: str = "MEDIUM"


@dataclass(frozen=True, slots=True)
class EmotionAnalysis:
    """Análisis emocional agregado."""

    primary_emotion: EmotionType
    secondary_emotions: tuple[EmotionType, ...] = ()
    emotional_intensity: float = 0.5
    emotional_arc_position: str = "UNKNOWN"
    energy_curve: str = "flat"
    emotional_transition: str = "none"


@dataclass(frozen=True, slots=True)
class VisualIntent:
    """Intención visual cinematográfica derivada de texto."""

    intent_type: VisualIntentKind
    cinematic_priority: float = 0.5
    suggested_camera_styles: tuple[str, ...] = ()
    suggested_editing_styles: tuple[str, ...] = ()
    suggested_visual_elements: tuple[str, ...] = ()
    suggested_motion: tuple[str, ...] = ()
    suggested_color_mood: tuple[str, ...] = ()
    suggested_transition_style: tuple[str, ...] = ()
    suggested_shot_types: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ClipSemanticMetadata:
    """Metadata semántica enriquecida asociada a un clip."""

    clip_id: str
    visual_description: str = ""
    primary_emotion: EmotionType | None = None
    secondary_emotions: tuple[EmotionType, ...] = ()
    energy_level: EnergyLevel | None = None
    pacing: Pacing | None = None
    camera_type: CameraType | None = None
    camera_movement: CameraMovement | None = None
    framing: Framing | None = None
    lighting_style: LightingStyle | None = None
    color_mood: ColorMood | None = None
    cinematic_style: CinematicStyle | None = None
    marketing_usage: MarketingUsage | None = None
    narrative_roles: tuple[NarrativeRole, ...] = ()
    visual_intents: tuple[str, ...] = ()
    objects_detected: tuple[str, ...] = ()
    actions_detected: tuple[str, ...] = ()
    people_detected: tuple[str, ...] = ()
    environment_type: EnvironmentType | None = None
    transition_compatibility: TransitionCompatibility | None = None
    hook_strength: float = 0.0
    cta_strength: float = 0.0
    emotional_intensity: float = 0.0
    semantic_tags: tuple[str, ...] = ()
    searchable_keywords: tuple[str, ...] = ()
    embedding_vector_id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class SmartRankingInput:
    """Factores de entrada para ranking multi-factor (0..1 donde aplique)."""

    semantic_similarity: float = 0.0
    emotional_compatibility: float = 0.0
    narrative_compatibility: float = 0.0
    pacing_compatibility: float = 0.0
    cinematic_compatibility: float = 0.0
    visual_intent_compatibility: float = 0.0
    feedback_score: float = 0.0
    historical_performance: float = 0.0


@dataclass(slots=True)
class SmartRankingBreakdown:
    """Desglose auditable del score."""

    final_score: float
    weighted: dict[str, float]
    weights_used: dict[str, float]


@dataclass(slots=True)
class FeedbackEvent:
    """Evento de feedback del usuario (dominio)."""

    id: str
    event_type: str
    clip_id: str | None = None
    scene_id: str | None = None
    project_id: str | None = None
    rejection_reason: str | None = None
    acceptance_score: float | None = None
    payload: dict[str, Any] | None = None
