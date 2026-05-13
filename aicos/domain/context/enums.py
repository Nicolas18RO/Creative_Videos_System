"""Enumeraciones del contexto global."""

from __future__ import annotations

from enum import StrEnum


class NarrativeArc(StrEnum):
    """Arco narrativo dominante del audio completo."""

    PROBLEM_SOLUTION = "problem_solution"
    AWARENESS_CONSIDERATION = "awareness_consideration"
    SOCIAL_PROOF_HEAVY = "social_proof_heavy"
    EDUCATIONAL = "educational"
    PROMOTIONAL = "promotional"
    STORY_ARC = "story_arc"
    TESTIMONIAL = "testimonial"
    UNKNOWN = "unknown"
    AMBIGUOUS = "ambiguous"


class IndustryType(StrEnum):
    """Industria inferida (tópico dominante)."""

    AUTOMOTIVE = "automotive"
    COSMETICS = "cosmetics"
    MEDICAL = "medical"
    FITNESS = "fitness"
    TECH = "tech"
    FINANCE = "finance"
    HOME = "home"
    FOOD = "food"
    EDUCATION = "education"
    GENERAL = "general"


class VisualStyle(StrEnum):
    """Estilo visual cinematográfico sugerido para el proyecto."""

    MECHANICAL_CINEMATIC = "mechanical_cinematic"
    BEAUTY_SOFT_LIGHT = "beauty_soft_light"
    CLINICAL_CLEAN = "clinical_clean"
    UGC_HANDHELD = "ugc_handheld"
    LIFESTYLE_WARM = "lifestyle_warm"
    TECH_MINIMAL = "tech_minimal"
    FOOD_APPETITE = "food_appetite"
    UNKNOWN = "unknown"


class ContextIntent(StrEnum):
    """Intención de contenido del pieza."""

    PERSUADE = "persuade"
    EDUCATE = "educate"
    ENTERTAIN = "entertain"
    WARN = "warn"
    INSPIRE = "inspire"
    UNKNOWN = "unknown"
