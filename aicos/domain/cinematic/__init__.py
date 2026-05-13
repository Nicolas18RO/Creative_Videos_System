"""Dominio puro: inteligencia cinematográfica y semántica (sin I/O ni frameworks)."""

from aicos.domain.cinematic.entities import (
    ClipSemanticMetadata,
    EmotionAnalysis,
    NarrativeClassificationResult,
    VisualIntent,
)
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
)

__all__ = [
    "CameraMovement",
    "CameraType",
    "ClipSemanticMetadata",
    "CinematicStyle",
    "ColorMood",
    "EmotionAnalysis",
    "EmotionType",
    "EnergyLevel",
    "EnvironmentType",
    "Framing",
    "LightingStyle",
    "MarketingUsage",
    "NarrativeClassificationResult",
    "NarrativeRole",
    "Pacing",
    "TransitionCompatibility",
    "VisualIntent",
]
