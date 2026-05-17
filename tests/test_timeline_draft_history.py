"""Tests utilidades de historial (patrón undo/redo, Fase 6.8)."""

from aicos.domain.editorial_training.timeline_rules import SceneBoundary, validate_scene_boundaries


def test_precision_preserved_in_validation():
    scenes = (
        SceneBoundary(0, 15.2, 18.5),
        SceneBoundary(1, 18.5, 22.0),
    )
    result = validate_scene_boundaries(scenes)
    assert result.valid
    assert result.normalized[0].start_time == 15.2


def test_overlap_at_millisecond_level():
    scenes = (
        SceneBoundary(5, 14.0, 15.0),
        SceneBoundary(6, 14.999, 16.0),
    )
    result = validate_scene_boundaries(scenes, max_gap=0.0)
    assert not result.valid
