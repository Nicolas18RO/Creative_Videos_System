"""Tests del constructor de texto semántico."""

from aicos.taxonomy.parser import parse_filename
from aicos.taxonomy.text_builder import build_semantic_text


def test_semantic_text_knee_stairs() -> None:
    name = "F_PROBLEM_KNEE_PAIN_STAIRS_01.mp4"
    t = parse_filename(name)
    text = build_semantic_text(t, name)
    assert "knee" in text.lower()
    assert "problem" in text.lower() or "pain" in text.lower()
    assert "stairs" in text.lower() or "woman" in text.lower()


def test_semantic_text_noncompliant_fallback() -> None:
    name = "clearzal pain relieving gel 03(12)-1.mp4"
    t = parse_filename(name)
    text = build_semantic_text(t, name)
    assert "clearzal" in text.lower()
