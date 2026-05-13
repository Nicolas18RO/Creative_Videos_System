"""Enumeraciones fuertemente tipadas para metadata y narrativa."""

from __future__ import annotations

from enum import StrEnum


class NarrativeRole(StrEnum):
    """Rol narrativo de un fragmento (VSL, UGC, short-form)."""

    HOOK = "HOOK"
    PROBLEM = "PROBLEM"
    AGITATION = "AGITATION"
    SOLUTION = "SOLUTION"
    BENEFIT = "BENEFIT"
    SOCIAL_PROOF = "SOCIAL_PROOF"
    DEMONSTRATION = "DEMONSTRATION"
    TESTIMONIAL = "TESTIMONIAL"
    CTA = "CTA"
    TRANSITION = "TRANSITION"
    EDUCATIONAL = "EDUCATIONAL"
    STORYTELLING = "STORYTELLING"
    EMOTIONAL_PEAK = "EMOTIONAL_PEAK"
    CURIOSITY_LOOP = "CURIOSITY_LOOP"
    BEFORE_AFTER = "BEFORE_AFTER"
    UNKNOWN = "UNKNOWN"


class EmotionType(StrEnum):
    """Emociones de marketing / tono."""

    FEAR = "FEAR"
    URGENCY = "URGENCY"
    TRUST = "TRUST"
    JOY = "JOY"
    SADNESS = "SADNESS"
    CURIOSITY = "CURIOSITY"
    EXCITEMENT = "EXCITEMENT"
    RELIEF = "RELIEF"
    ANXIETY = "ANXIETY"
    SURPRISE = "SURPRISE"
    CONFIDENCE = "CONFIDENCE"
    ASPIRATION = "ASPIRATION"
    EMPATHY = "EMPATHY"
    TENSION = "TENSION"
    DESIRE = "DESIRE"
    PAIN = "PAIN"
    HOPE = "HOPE"
    MOTIVATION = "MOTIVATION"
    NEUTRAL = "NEUTRAL"


class EnergyLevel(StrEnum):
    VERY_LOW = "VERY_LOW"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"


class Pacing(StrEnum):
    SLOW = "SLOW"
    MEDIUM = "MEDIUM"
    FAST = "FAST"
    VARIED = "VARIED"


class CameraType(StrEnum):
    HANDHELD = "HANDHELD"
    TRIPOD = "TRIPOD"
    GIMBAL = "GIMBAL"
    DRONE = "DRONE"
    STATIC = "STATIC"
    OTHER = "OTHER"


class CameraMovement(StrEnum):
    STATIC = "STATIC"
    PAN = "PAN"
    TILT = "TILT"
    DOLLY = "DOLLY"
    ZOOM = "ZOOM"
    ORBIT = "ORBIT"
    WHIP = "WHIP"
    OTHER = "OTHER"


class Framing(StrEnum):
    EXTREME_WIDE = "EXTREME_WIDE"
    WIDE = "WIDE"
    MEDIUM = "MEDIUM"
    CLOSE_UP = "CLOSE_UP"
    EXTREME_CLOSE_UP = "EXTREME_CLOSE_UP"
    OTHER = "OTHER"


class LightingStyle(StrEnum):
    NATURAL = "NATURAL"
    STUDIO = "STUDIO"
    HIGH_KEY = "HIGH_KEY"
    LOW_KEY = "LOW_KEY"
    NEON = "NEON"
    GOLDEN_HOUR = "GOLDEN_HOUR"
    OTHER = "OTHER"


class ColorMood(StrEnum):
    WARM = "WARM"
    COOL = "COOL"
    DESATURATED = "DESATURATED"
    VIBRANT = "VIBRANT"
    MONOCHROME = "MONOCHROME"
    OTHER = "OTHER"


class CinematicStyle(StrEnum):
    UGC = "UGC"
    CINEMATIC = "CINEMATIC"
    COMMERCIAL = "COMMERCIAL"
    DOCUMENTARY = "DOCUMENTARY"
    VLOG = "VLOG"
    TIKTOK_NATIVE = "TIKTOK_NATIVE"
    VSL = "VSL"
    OTHER = "OTHER"


class MarketingUsage(StrEnum):
    AWARENESS = "AWARENESS"
    CONSIDERATION = "CONSIDERATION"
    CONVERSION = "CONVERSION"
    RETENTION = "RETENTION"
    BRAND = "BRAND"
    SOCIAL_PROOF_USE = "SOCIAL_PROOF_USE"
    OTHER = "OTHER"


class EnvironmentType(StrEnum):
    INDOOR = "INDOOR"
    OUTDOOR = "OUTDOOR"
    STUDIO = "STUDIO"
    MIXED = "MIXED"
    OTHER = "OTHER"


class TransitionCompatibility(StrEnum):
    MATCH_CUT = "MATCH_CUT"
    J_CUT = "J_CUT"
    HARD_CUT = "HARD_CUT"
    DISSOLVE = "DISSOLVE"
    SWIPE = "SWIPE"
    OTHER = "OTHER"


class VisualIntentKind(StrEnum):
    """Tipos de intención visual inferida desde texto."""

    URGENCY = "urgency"
    COUNTDOWN = "countdown"
    FAST_PACING = "fast_pacing"
    PRODUCT_CLOSEUP = "product_closeup"
    HIGH_ATTENTION = "high_attention"
    EMOTIONAL_REACTION = "emotional_reaction"
    TRUST_BUILDING = "trust_building"
    SOCIAL_PROOF_VISUAL = "social_proof_visual"
    BEFORE_AFTER_VISUAL = "before_after_visual"
    EDUCATIONAL_GRAPHIC = "educational_graphic"
    HOOK_VISUAL = "hook_visual"
    CTA_VISUAL = "cta_visual"
    GENERIC = "generic"
