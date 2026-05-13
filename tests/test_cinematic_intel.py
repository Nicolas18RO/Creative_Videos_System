"""Tests unitarios para inteligencia cinematográfica (local-first)."""

from __future__ import annotations

import pytest

from aicos.application.cinematic.narrative_classifier_service import NarrativeClassifierService
from aicos.application.cinematic.providers.future_openai_narrative import FutureOpenAINarrativeProvider
from aicos.application.cinematic.providers.local_llm_narrative import LocalLLMNarrativeProvider
from aicos.application.cinematic.rule_based_narrative import RuleBasedNarrativeProvider
from aicos.application.cinematic.rule_based_emotion import RuleBasedEmotionAnalyzer
from aicos.application.cinematic.rule_based_visual_intent import RuleBasedVisualIntentExtractor
from aicos.application.cinematic.smart_clip_ranking import SmartClipRankingService
from aicos.application.cinematic.ranking_signals import emotional_compatibility, narrative_compatibility
from aicos.config import CinematicIntelConfig
from aicos.domain.cinematic.entities import (
    ClipSemanticMetadata,
    EmotionAnalysis,
    SmartRankingInput,
)
from aicos.domain.cinematic.enums import EmotionType, NarrativeRole, Pacing
from aicos.services.cinematic_intel_repository import clip_meta_to_payload, payload_to_clip_meta


def test_rule_narrative_cta_spanish() -> None:
    p = RuleBasedNarrativeProvider()
    r = p.classify("", "Compra ya con el link en bio", None)
    assert r is not None
    assert r.narrative_role == NarrativeRole.CTA
    assert r.confidence >= 0.45


def test_rule_emotion_urgency() -> None:
    a = RuleBasedEmotionAnalyzer()
    out = a.analyze("", "Esta oferta termina hoy", pacing_hint="FAST")
    assert out.primary_emotion == EmotionType.URGENCY


def test_visual_intent_urgency_phrase() -> None:
    ex = RuleBasedVisualIntentExtractor()
    intents = ex.extract("", "Esta oferta termina hoy")
    labels = [i.intent_type.value for i in intents]
    assert "urgency" in labels


def test_narrative_classifier_chain_falls_through_to_rules() -> None:
    svc = NarrativeClassifierService(
        providers=[
            LocalLLMNarrativeProvider(enabled=False),
            FutureOpenAINarrativeProvider(),
            RuleBasedNarrativeProvider(),
        ],
        provider_order=("local_llm", "future_openai", "rules"),
    )
    out, prov = svc.classify("", "buy now limited time", None)
    assert prov == "rules"
    assert out.narrative_role == NarrativeRole.CTA


def test_smart_ranking_weights() -> None:
    cfg = CinematicIntelConfig()
    svc = SmartClipRankingService(config=cfg)
    inp = SmartRankingInput(
        semantic_similarity=0.8,
        emotional_compatibility=0.7,
        narrative_compatibility=0.6,
        pacing_compatibility=0.5,
        cinematic_compatibility=0.4,
        visual_intent_compatibility=0.9,
        feedback_score=0.2,
        historical_performance=0.3,
    )
    b = svc.score(inp)
    assert 0.0 <= b.final_score <= 1.0
    assert set(b.weighted.keys()) == set(b.weights_used.keys())


def test_clip_metadata_json_roundtrip() -> None:
    meta = ClipSemanticMetadata(
        clip_id="abc",
        narrative_roles=(NarrativeRole.HOOK,),
        pacing=Pacing.FAST,
        primary_emotion=EmotionType.CURIOSITY,
        visual_intents=("urgency",),
        semantic_tags=("HOOK",),
    )
    payload = clip_meta_to_payload(meta)
    back = payload_to_clip_meta("abc", payload)
    assert back.clip_id == "abc"
    assert back.narrative_roles == (NarrativeRole.HOOK,)
    assert back.pacing == Pacing.FAST


def test_ranking_signals_emotion_match() -> None:
    scene = EmotionAnalysis(
        primary_emotion=EmotionType.JOY,
        secondary_emotions=(EmotionType.TRUST,),
        emotional_intensity=0.8,
    )
    clip = ClipSemanticMetadata(clip_id="x", primary_emotion=EmotionType.JOY)
    assert emotional_compatibility(scene, clip) == 1.0
    clip2 = ClipSemanticMetadata(clip_id="x", primary_emotion=EmotionType.TRUST)
    assert emotional_compatibility(scene, clip2) == 0.82


def test_ranking_signals_narrative() -> None:
    clip = ClipSemanticMetadata(clip_id="x", narrative_roles=(NarrativeRole.CTA,))
    assert narrative_compatibility(NarrativeRole.CTA, clip) == 1.0


def test_factory_builds_pipeline() -> None:
    from aicos.services.cinematic_intel_factory import build_clip_intelligence_pipeline

    pipe = build_clip_intelligence_pipeline()
    assert pipe.frame_extractor is not None
