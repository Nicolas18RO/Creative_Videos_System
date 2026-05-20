"""Tests dominio editorial_taxonomy — separación clip vs narrativa."""

from aicos.domain.editorial_taxonomy.rules import (
    effective_clip_source_taxonomy,
    effective_narrative_intent,
    infer_emotional_intent_from_text,
    should_persist_human_override,
    normalize_clip_source_taxonomy,
    normalize_narrative_intent,
)


def test_clip_and_narrative_independent():
    assert effective_clip_source_taxonomy("AUTHORITY", None) == "AUTHORITY"
    assert effective_narrative_intent("PROBLEM", "PROBLEM") == "PROBLEM"
    assert effective_narrative_intent("PROBLEM", "AUTHORITY") == "AUTHORITY"


def test_human_narrative_override_persists_when_different_from_auto():
    assert should_persist_human_override("PROBLEM", "AUTHORITY", normalizer=normalize_narrative_intent)


def test_emotional_from_spanish_audio():
    assert infer_emotional_intent_from_text("tu hígado se destruye lentamente") == "FEAR"
