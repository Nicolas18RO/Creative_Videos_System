"""Reglas puras: taxonomía de carpeta del clip ≠ intención narrativa del audio."""

from __future__ import annotations

CLIP_SOURCE_TAXONOMIES: tuple[str, ...] = (
    "HOOK",
    "PROBLEM",
    "BENEFIT",
    "RESULT",
    "AUTHORITY",
    "SOCIAL_PROOF",
    "PRODUCT",
    "CTA",
    "NATURAL",
)

NARRATIVE_INTENTS: tuple[str, ...] = CLIP_SOURCE_TAXONOMIES

EDITORIAL_EMOTIONAL_INTENTS: tuple[str, ...] = (
    "FEAR",
    "HOPE",
    "URGENCY",
    "TRUST",
    "CURIOSITY",
    "EMPATHY",
    "NEUTRAL",
)


def _normalize(value: str | None, allowed: tuple[str, ...], *, default: str) -> str:
    r = (value or "").strip().upper().replace(" ", "_")
    if r in allowed:
        return r
    return default if not r else r


def normalize_clip_source_taxonomy(value: str | None, *, default: str = "NATURAL") -> str:
    return _normalize(value, CLIP_SOURCE_TAXONOMIES, default=default)


def normalize_narrative_intent(value: str | None, *, default: str = "NATURAL") -> str:
    return _normalize(value, NARRATIVE_INTENTS, default=default)


def normalize_emotional_intent(value: str | None, *, default: str = "NEUTRAL") -> str:
    return _normalize(value, EDITORIAL_EMOTIONAL_INTENTS, default=default)


def effective_clip_source_taxonomy(auto: str, human: str | None) -> str:
    if human and str(human).strip():
        return normalize_clip_source_taxonomy(human)
    return normalize_clip_source_taxonomy(auto)


def effective_narrative_intent(auto: str, human: str | None) -> str:
    if human and str(human).strip():
        return normalize_narrative_intent(human)
    return normalize_narrative_intent(auto)


def effective_emotional_intent(auto: str, human: str | None) -> str:
    if human and str(human).strip():
        return normalize_emotional_intent(human)
    return normalize_emotional_intent(auto)


def should_persist_human_override(auto_value: str, proposed_human: str, *, normalizer) -> bool:
    auto_n = normalizer(auto_value)
    human_n = normalizer(proposed_human)
    return human_n != auto_n


def taxonomy_auto_must_not_be_overwritten(existing_auto: str, incoming_auto: str, *, normalizer) -> str:
    if (existing_auto or "").strip():
        return normalizer(existing_auto)
    return normalizer(incoming_auto)


def intent_label_for_role(role: str) -> str:
    nr = normalize_narrative_intent(role)
    if nr == "HOOK":
        return "Hook Scene"
    if nr == "CTA":
        return "Call To Action"
    if nr == "PRODUCT":
        return "Product Scene"
    if nr:
        return nr.replace("_", " ").title()
    return "Scene"


def infer_emotional_intent_from_text(audio_text: str, concept: str = "") -> str:
    blob = f"{audio_text} {concept}".lower()
    if any(w in blob for w in ("miedo", "colaps", "destruy", "pánico", "terror", "fatal", "grave")):
        return "FEAR"
    if any(w in blob for w in ("urgent", "ahora", "rápido", "inmediat", "últim")):
        return "URGENCY"
    if any(w in blob for w in ("confía", "doctor", "ciencia", "estudio", "probado")):
        return "TRUST"
    if any(w in blob for w in ("descubr", "secret", "sabías", "imagina")):
        return "CURIOSITY"
    if any(w in blob for w in ("esperanz", "mejor", "recuper", "solución", "alivio")):
        return "HOPE"
    if any(w in blob for w in ("sientes", "entiendo", "como tú", "solo")):
        return "EMPATHY"
    return "NEUTRAL"


def infer_visual_style_label(*, subcategory: str = "", semantic_tags: tuple[str, ...] = ()) -> str:
    sub = (subcategory or "").strip().upper()
    tags = " ".join(semantic_tags).upper()
    if "ANIMATION" in sub or "ANIMATION" in tags:
        if "MEDICAL" in sub or "KNEE" in sub or "EYE" in sub or "CELL" in sub:
            return "Animated medical visualization"
        return "Animated visualization"
    if sub in ("TESTIMONIAL_SELFIE", "CHIROPRACTOR_TALKING"):
        return "Talking head / testimonial"
    if sub in ("RAW_INGREDIENT", "INGREDIENT_SOURCE", "LABORATORY"):
        return "Product / ingredient b-roll"
    if tags:
        return tags.replace("_", " ").title()[:80]
    return "Live action b-roll"
