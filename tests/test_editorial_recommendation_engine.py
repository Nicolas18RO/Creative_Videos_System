"""Tests Fase 6.5 — motor de recomendaciones editoriales."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

from aicos.application.editorial_recommendation_engine.editorial_recommendation_service import (
    EditorialRecommendationService,
)
from aicos.config import EditorialRecommendationEngineConfig
from aicos.domain.editorial_dataset.entities import (
    CreativeStyleProfile,
    CreativeTimeline,
    EditorialPattern,
    EditorialStyleSignals,
    TimelineScene,
)
from aicos.domain.editorial_recommendation.plan_builder import build_editorial_recommendation_plan
from aicos.domain.editorial_recommendation.entities import StyleMemoryPeerRef
from aicos.domain.editorial_style_retrieval.entities import StyleSimilarityHit


def _timeline(cid: str = "t1") -> CreativeTimeline:
    scenes = (
        TimelineScene(
            scene_index=0,
            clip_id="a",
            start_time=0.0,
            end_time=1.0,
            duration=1.0,
            transition_type="cut",
            narrative_role="hook",
            motion_intensity=0.7,
            visual_energy=0.6,
            camera_type="wide",
            semantic_tags=("producto",),
            emotion_tags=("curiosidad",),
        ),
        TimelineScene(
            scene_index=1,
            clip_id="b",
            start_time=1.0,
            end_time=2.5,
            duration=1.5,
            transition_type="cut",
            narrative_role="body",
            motion_intensity=0.5,
            visual_energy=0.5,
            camera_type="macro",
            semantic_tags=("detalle",),
            emotion_tags=("confianza",),
        ),
    )
    sp = CreativeStyleProfile(
        hook_intensity=0.8,
        average_pacing=0.75,
        motion_density=0.5,
        transition_density=0.3,
        narrative_aggressiveness=0.4,
        visual_dynamism=0.55,
        cinematic_style_tags=("clean", "macro_heavy"),
    )
    ss = EditorialStyleSignals(
        pacing_score=0.8,
        hook_strength=0.7,
        emotional_curve=(0.5, 0.6),
        visual_dynamism=0.55,
    )
    pat = (
        EditorialPattern(
            pattern_id="p1",
            pattern_type="cut_burst",
            pattern_sequence=("HOOK", "BODY", "BODY"),
            frequency=0.4,
            confidence_score=0.75,
        ),
    )
    return CreativeTimeline(
        creative_id=cid,
        audio_path="",
        final_video_path="",
        timeline_scenes=scenes,
        style_profile=sp,
        style_signals=ss,
        editorial_patterns=pat,
        hook_detection=(),
        created_at=datetime.now(timezone.utc),
    )


class _FakeTimelineRead:
    def __init__(self, t: CreativeTimeline | None) -> None:
        self._t = t

    def get_by_creative_id(self, session, creative_id: str):  # noqa: ARG002
        if self._t is None:
            return None
        return self._t if self._t.creative_id == creative_id else None


class _FakeStylePort:
    def __init__(self, hits: tuple[StyleSimilarityHit, ...]) -> None:
        self._hits = hits

    def retrieve_hits(self, session, anchor_creative_id: str, top_k: int):  # noqa: ARG002
        return self._hits[:top_k]


def test_plan_builder_includes_pacing_and_clip_hint() -> None:
    t = _timeline()
    peers = (StyleMemoryPeerRef("peer_a", 0.81),)
    plan = build_editorial_recommendation_plan(t, peers, pacing_high_threshold=0.72, pacing_low_threshold=0.35)
    kinds = {i.kind for i in plan.items}
    assert "pacing" in kinds
    assert "style_memory" in kinds
    assert "clip_search" in kinds
    assert plan.clip_search_hint is not None
    assert plan.clip_search_hint.narrative_function_hint == "BODY"


def test_service_with_style_memory() -> None:
    hits = (
        StyleSimilarityHit(
            creative_id="peer1",
            rank=1,
            structural_similarity=0.9,
            semantic_similarity=None,
            hybrid_score=0.85,
            peer_digest_sha256="b" * 64,
        ),
    )
    cfg = EditorialRecommendationEngineConfig(
        enabled=True,
        use_style_memory=True,
        style_memory_top_k=3,
        style_memory_min_peer_score=0.1,
    )
    svc = EditorialRecommendationService(cfg, _FakeTimelineRead(_timeline()), _FakeStylePort(hits))
    plan = svc.build_plan(MagicMock(), creative_id="t1")
    assert plan is not None
    assert len(plan.style_memory_peers) == 1
    assert plan.style_memory_peers[0].creative_id == "peer1"


def test_service_disabled_returns_none() -> None:
    cfg = EditorialRecommendationEngineConfig(enabled=False)
    svc = EditorialRecommendationService(cfg, _FakeTimelineRead(_timeline()), _FakeStylePort(()))
    assert svc.build_plan(MagicMock(), creative_id="t1") is None


def test_service_missing_timeline() -> None:
    cfg = EditorialRecommendationEngineConfig(enabled=True, use_style_memory=False)
    svc = EditorialRecommendationService(cfg, _FakeTimelineRead(None), None)
    assert svc.build_plan(MagicMock(), creative_id="x") is None
