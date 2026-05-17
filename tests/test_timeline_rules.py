"""Tests dominio Fase 6.8 — reglas de timeline."""

from aicos.domain.editorial_training.timeline_rules import (
    SceneBoundary,
    detect_invalid_overlaps,
    detect_negative_gaps,
    normalize_scene_boundaries,
    validate_scene_boundaries,
)


def test_overlap_detected():
    scenes = (
        SceneBoundary(0, 0.0, 5.0),
        SceneBoundary(1, 4.9, 10.0),
    )
    result = validate_scene_boundaries(scenes)
    assert not result.valid
    assert any(i.code == "overlap" for i in result.issues)


def test_negative_gap_detected():
    scenes = (
        SceneBoundary(0, 0.0, 5.0),
        SceneBoundary(1, 4.8, 10.0),
    )
    result = validate_scene_boundaries(scenes, max_gap=0.0)
    assert any(i.code in ("overlap", "negative_gap") for i in result.issues)


def test_normalize_rounds_to_milliseconds():
    scenes = (SceneBoundary(0, 15.2004, 18.9996),)
    norm = normalize_scene_boundaries(scenes)
    assert norm[0].start_time == 15.2
    assert norm[0].end_time == 19.0


def test_valid_adjacent_scenes():
    scenes = (
        SceneBoundary(0, 0.0, 5.0),
        SceneBoundary(1, 5.0, 10.0),
    )
    result = validate_scene_boundaries(scenes)
    assert result.valid


def test_detect_helpers():
    left = SceneBoundary(0, 0.0, 5.0)
    right = SceneBoundary(1, 4.9, 8.0)
    assert detect_invalid_overlaps(left, right)
    assert detect_negative_gaps(-0.1)
