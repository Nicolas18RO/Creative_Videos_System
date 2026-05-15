"""Tests de mapeo escenas analizadas → timeline editorial (Fase 6.7)."""

from __future__ import annotations

from aicos.application.editorial_training.analyzed_scene_to_timeline import map_analyzed_scenes_to_raw_inputs
from aicos.models.schemas import AnalyzedScene, Recommendation, Scene


def _reco(clip_id: str) -> Recommendation:
    return Recommendation(
        clip_id=clip_id,
        clip_path="/tmp/x.mp4",
        rank=1,
        similarity_score=0.9,
        taxonomy_boost=0.0,
        final_score=0.9,
    )


def test_map_uses_first_recommendation_clip_id() -> None:
    sc = Scene(
        scene_id="a",
        scene_index=1,
        start_ms=1000,
        end_ms=3000,
        duration_ms=2000,
        text="hola",
        narrative_function="BENEFIT",
        is_hook=False,
        hook_score=0.1,
    )
    asc = AnalyzedScene(scene=sc, recommendations=[_reco("clip_z")], is_gap=False, gap=None)
    raw = map_analyzed_scenes_to_raw_inputs([asc])
    assert len(raw) == 1
    assert raw[0].clip_id == "clip_z"
    assert raw[0].scene_index == 1
    assert raw[0].start_time == 1.0
    assert raw[0].end_time == 3.0
    assert raw[0].narrative_role == "BENEFIT"


def test_map_unassigned_without_recommendations() -> None:
    sc = Scene(
        scene_id="b",
        scene_index=0,
        start_ms=0,
        end_ms=500,
        duration_ms=500,
        text="hook",
        narrative_function="HOOK",
        is_hook=True,
        hook_score=0.9,
    )
    asc = AnalyzedScene(scene=sc, recommendations=[], is_gap=True, gap=None)
    raw = map_analyzed_scenes_to_raw_inputs([asc])
    assert raw[0].clip_id == "unassigned_0"
    assert raw[0].visual_energy >= 0.5
