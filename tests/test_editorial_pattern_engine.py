"""Tests del motor de patrones editoriales Fase 6.2."""

from __future__ import annotations

from aicos.application.editorial_pattern_engine.serialization import report_from_jsonable, report_to_jsonable
from aicos.domain.editorial_dataset.entities import (
    CreativeStyleProfile,
    CreativeTimeline,
    EditorialStyleSignals,
    TimelineScene,
)
from aicos.services.editorial_pattern_engine_factory import build_editorial_pattern_extraction_engine


def _timeline() -> CreativeTimeline:
    scenes = tuple(
        TimelineScene(
            scene_index=i,
            clip_id=f"c{i}",
            start_time=float(i) * 0.5,
            end_time=float(i) * 0.5 + 0.45,
            duration=0.45,
            transition_type="whip" if i == 0 else "cut",
            narrative_role="hook_open" if i == 0 else "body",
            motion_intensity=0.7 if i < 2 else 0.4,
            visual_energy=0.75 if i < 2 else 0.45,
            camera_type="handheld",
            semantic_tags=("x",),
            emotion_tags=("tension",),
        )
        for i in range(5)
    )
    profile = CreativeStyleProfile(
        hook_intensity=0.0,
        average_pacing=0.5,
        motion_density=0.0,
        transition_density=0.0,
        narrative_aggressiveness=0.0,
        visual_dynamism=0.0,
        cinematic_style_tags=(),
    )
    signals = EditorialStyleSignals(
        pacing_score=0.0, hook_strength=0.0, emotional_curve=tuple(), visual_dynamism=0.0
    )
    return CreativeTimeline(
        creative_id="eng_test",
        audio_path="",
        final_video_path="",
        timeline_scenes=scenes,
        style_profile=profile,
        style_signals=signals,
    )


def test_engine_build_report_without_session() -> None:
    engine = build_editorial_pattern_extraction_engine(None)
    t = _timeline()
    rep = engine.build_report(t, None)
    assert rep.engine_version.startswith("6.2")
    assert len(rep.enriched_scenes) == 5
    assert rep.cut_rhythm.cuts_per_minute > 0
    assert len(rep.momentum.momentum_samples) == 5


def test_roundtrip_serialization() -> None:
    engine = build_editorial_pattern_extraction_engine(None)
    rep = engine.build_report(_timeline(), None)
    js = report_to_jsonable(rep)
    back = report_from_jsonable(js)
    assert back is not None
    assert len(back.enriched_scenes) == 5
    assert abs(back.cut_rhythm.cuts_per_minute - rep.cut_rhythm.cuts_per_minute) < 1e-6