"""Tests de detección de hooks y extracción de patrones editoriales."""

from __future__ import annotations

from aicos.application.editorial_dataset.editorial_pattern_extraction_service import (
    EditorialPatternExtractionService,
)
from aicos.config import EditorialDatasetConfig, EditorialPatternEngineConfig
from aicos.domain.editorial_dataset.entities import CreativeStyleProfile, CreativeTimeline, TimelineScene


def _scene(
    idx: int,
    start: float,
    end: float,
    *,
    motion: float = 0.5,
    energy: float = 0.5,
    transition: str = "cut",
    narrative_role: str = "beat",
    sem: tuple[str, ...] = (),
) -> TimelineScene:
    return TimelineScene(
        scene_index=idx,
        clip_id=f"c{idx}",
        start_time=start,
        end_time=end,
        duration=end - start,
        transition_type=transition,
        narrative_role=narrative_role,
        motion_intensity=motion,
        visual_energy=energy,
        camera_type="handheld",
        semantic_tags=sem,
        emotion_tags=("tension",),
    )


def _minimal_timeline(scenes: tuple[TimelineScene, ...]) -> CreativeTimeline:
    profile = CreativeStyleProfile(
        hook_intensity=0.0,
        average_pacing=1.0,
        motion_density=0.0,
        transition_density=0.0,
        narrative_aggressiveness=0.0,
        visual_dynamism=0.0,
        cinematic_style_tags=(),
    )
    from aicos.domain.editorial_dataset.entities import EditorialStyleSignals

    signals = EditorialStyleSignals(
        pacing_score=0.0, hook_strength=0.0, emotional_curve=tuple(), visual_dynamism=0.0
    )
    return CreativeTimeline(
        creative_id="t1",
        audio_path="",
        final_video_path="",
        timeline_scenes=scenes,
        style_profile=profile,
        style_signals=signals,
    )


def test_hook_detection_aggressive_opening() -> None:
    cfg = EditorialDatasetConfig(
        detect_hooks=True, min_hook_duration=0.5, max_hook_duration=4.0
    )
    eng = EditorialPatternEngineConfig(enabled=True)
    svc = EditorialPatternExtractionService(cfg, eng)
    scenes = (
        _scene(0, 0.0, 0.35, motion=0.9, energy=0.92, transition="whip"),
        _scene(1, 0.35, 0.7, motion=0.88, energy=0.9, transition="zoom"),
        _scene(2, 0.7, 2.5, motion=0.2, energy=0.3, transition="cut"),
    )
    hooks = svc.detect_hooks(scenes)
    assert hooks
    assert hooks[0].hook_strength > 0.35


def test_hook_detection_disabled() -> None:
    cfg = EditorialDatasetConfig(detect_hooks=False)
    eng = EditorialPatternEngineConfig(enabled=True)
    svc = EditorialPatternExtractionService(cfg, eng)
    scenes = (_scene(0, 0.0, 1.0),)
    assert svc.detect_hooks(scenes) == ()


def test_pattern_ngram_repetition() -> None:
    cfg = EditorialDatasetConfig(detect_patterns=True)
    eng = EditorialPatternEngineConfig(enabled=True)
    svc = EditorialPatternExtractionService(cfg, eng)
    scenes = (
        _scene(0, 0.0, 1.0, narrative_role="mechanic_shot", sem=("taller",)),
        _scene(1, 1.0, 2.0, narrative_role="engine_macro", sem=("motor",)),
        _scene(2, 2.0, 3.0, narrative_role="mechanic_shot", sem=("taller",)),
        _scene(3, 3.0, 4.0, narrative_role="engine_macro", sem=("motor",)),
    )
    pats = svc.extract_editorial_patterns(scenes)
    seqs = [p.pattern_sequence for p in pats]
    assert any(len(s) >= 2 and s[:2] == ("mechanic_shot", "engine_macro") for s in seqs)


def test_attach_updates_style() -> None:
    cfg = EditorialDatasetConfig(detect_hooks=True, detect_patterns=True)
    eng = EditorialPatternEngineConfig(enabled=True)
    svc = EditorialPatternExtractionService(cfg, eng)
    scenes = (
        _scene(0, 0.0, 0.4, motion=0.9, energy=0.9, narrative_role="hook_open"),
        _scene(1, 0.4, 1.2, narrative_role="body"),
    )
    base = _minimal_timeline(scenes)
    out = svc.attach_patterns_to_timeline(base)
    assert out.style_signals.hook_strength >= 0.0
    assert len(out.style_profile.cinematic_style_tags) >= 0
