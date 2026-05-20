"""Taxonomía editorial: clip source vs intención narrativa (dominio puro)."""

from aicos.domain.editorial_taxonomy.entities import SceneSemanticIntent
from aicos.domain.editorial_taxonomy.rules import (
    CLIP_SOURCE_TAXONOMIES,
    EDITORIAL_EMOTIONAL_INTENTS,
    effective_clip_source_taxonomy,
    effective_emotional_intent,
    effective_narrative_intent,
    infer_emotional_intent_from_text,
    infer_visual_style_label,
    normalize_clip_source_taxonomy,
    normalize_emotional_intent,
    normalize_narrative_intent,
    should_persist_human_override,
    taxonomy_auto_must_not_be_overwritten,
)

__all__ = [
    "CLIP_SOURCE_TAXONOMIES",
    "EDITORIAL_EMOTIONAL_INTENTS",
    "SceneSemanticIntent",
    "effective_clip_source_taxonomy",
    "effective_emotional_intent",
    "effective_narrative_intent",
    "infer_emotional_intent_from_text",
    "infer_visual_style_label",
    "normalize_clip_source_taxonomy",
    "normalize_emotional_intent",
    "normalize_narrative_intent",
    "should_persist_human_override",
    "taxonomy_auto_must_not_be_overwritten",
]
