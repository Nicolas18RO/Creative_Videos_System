"""Tests del Contextual Retrieval Engine (Fase 2, post-Chroma)."""

from __future__ import annotations

import pytest

from aicos.application.cinematic.contextual_retrieval_service import (
    ContextualRetrievalService,
    RankingContext,
    RetrievalSignals,
    _automotive_mismatch,
    _contains_industry,
    _jaccard_tokens,
    get_contextual_retrieval_service,
)
from aicos.application.cinematic.continuity_analyzer_service import ContinuityAnalyzerService
from aicos.config import ContextualRetrievalConfig
from aicos.models.schemas import Recommendation, SearchRankingContext, SearchRequest


def _rec(
    clip_id: str,
    sim: float,
    *,
    text: str,
    sub: str = "generic",
    nf: str | None = "PROBLEM",
    final: float | None = None,
) -> Recommendation:
    boost = 0.0
    fs = final if final is not None else max(0.0, min(1.0, sim + boost))
    return Recommendation(
        clip_id=clip_id,
        clip_path=f"/clips/{clip_id}.mp4",
        rank=1,
        similarity_score=sim,
        taxonomy_boost=boost,
        final_score=fs,
        narrative_function=nf,
        clip_subcategory=sub,
        clip_context="",
        clip_semantic_text=text,
    )


def _rank_ctx(**kwargs: object) -> SearchRankingContext:
    defaults: dict[str, object] = {
        "industry": "general",
        "topic": "",
        "dominant_emotion": "neutral",
        "semantic_anchors": [],
        "narrative_arc": "unknown",
        "visual_style": "unknown",
        "content_intent": "unknown",
        "scene_text": "",
        "scene_concept": "",
        "narrative_function": None,
        "previous_selected_clip_ids": [],
        "prior_scene_concepts": [],
    }
    defaults.update(kwargs)
    return SearchRankingContext(**defaults)


def test_ranking_context_from_schema_maps_content_intent() -> None:
    s = SearchRankingContext(
        industry="automotive",
        content_intent="warn_engine_damage",
        semantic_anchors=("motor",),
    )
    rc = RankingContext.from_schema(s)
    assert rc.content_intent == "warn_engine_damage"
    assert rc.semantic_anchors == ("motor",)


def test_automotive_penalizes_food_not_engine() -> None:
    cfg = ContextualRetrievalConfig(
        enabled=True,
        lazy_rerank=False,
        diversity_balance_enabled=False,
        use_batch_context_embedding=False,
        weight_semantic=0.2,
        weight_global_context=0.25,
        weight_narrative=0.15,
        weight_domain=0.25,
        weight_emotion=0.05,
        weight_continuity=0.05,
        weight_cinematic_style=0.05,
    )
    svc = ContextualRetrievalService(cfg)
    req = SearchRequest(query="humo motor", candidate_pool_size=10, n_results=3)
    ranking = _rank_ctx(
        industry="automotive",
        semantic_anchors=["motor", "escape", "humo"],
        narrative_arc="problem_solution",
        narrative_function="PROBLEM",
        scene_text="el humo está destruyendo tu motor",
    )
    food = _rec("c1", 0.92, text="chef cocina receta pastel comida humo abstracto", sub="food", nf="BENEFIT")
    motor = _rec("c2", 0.88, text="closeup motor dañado humo de escape aceite taller mecánico", sub="repair", nf="PROBLEM")
    out = svc.apply_pipeline([food, motor], req, ranking, embedder=None)
    assert out[0].clip_id == "c2"


def test_cosmetics_prefers_beauty_blob() -> None:
    cfg = ContextualRetrievalConfig(
        enabled=True,
        lazy_rerank=False,
        diversity_balance_enabled=False,
        weight_semantic=0.25,
        weight_global_context=0.3,
        weight_domain=0.25,
        weight_narrative=0.1,
        weight_emotion=0.05,
        weight_continuity=0.025,
        weight_cinematic_style=0.025,
    )
    svc = ContextualRetrievalService(cfg)
    req = SearchRequest(query="piel radiante", candidate_pool_size=10, n_results=3)
    ranking = _rank_ctx(
        industry="cosmetics",
        semantic_anchors=["piel", "crema", "glow"],
        scene_text="hidrata tu piel",
    )
    wrong = _rec("w1", 0.9, text="piston motor aceite taller automotive", sub="auto", nf="HOOK")
    ok = _rec("w2", 0.87, text="crema facial piel suave beauty maquillaje glow", sub="skincare", nf="HOOK")
    out = svc.apply_pipeline([wrong, ok], req, ranking, embedder=None)
    assert out[0].clip_id == "w2"


def test_emotion_concern_matches_damage_spanish() -> None:
    cfg = ContextualRetrievalConfig(enabled=True, lazy_rerank=False, diversity_balance_enabled=False)
    svc = ContextualRetrievalService(cfg)
    ranking = _rank_ctx(
        industry="automotive",
        dominant_emotion="concern",
        scene_text="daño irreversible al bloque",
        semantic_anchors=["motor"],
    )
    r = _rec("e1", 0.8, text="motor dañado riesgo peligro", nf="PROBLEM")
    req = SearchRequest(query="daño", candidate_pool_size=5, n_results=2)
    out = svc.apply_pipeline([r], req, ranking, embedder=None)
    assert out[0].final_score >= 0.0


def test_continuity_repeat_clip_penalized() -> None:
    cont = ContinuityAnalyzerService()
    rec = _rec("used-1", 0.95, text="motor humo", nf="PROBLEM")
    ctx = _rank_ctx(previous_selected_clip_ids=["used-1"], prior_scene_concepts=["motor turbo"])
    assert cont.score(rec, ctx) == pytest.approx(0.15, abs=0.01)


def test_continuity_prior_concepts_jaccard() -> None:
    cont = ContinuityAnalyzerService()
    rec = _rec("x", 0.5, text="turbo motor aceite mismo taller", nf="PROBLEM")
    ctx = _rank_ctx(prior_scene_concepts=["falla turbo aceite"])
    s = cont.score(rec, ctx)
    assert s > 0.45


def test_semantic_anchor_substring_boost() -> None:
    cfg = ContextualRetrievalConfig(
        enabled=True,
        lazy_rerank=False,
        diversity_balance_enabled=False,
        weight_semantic=0.15,
        weight_global_context=0.45,
        weight_domain=0.15,
        weight_narrative=0.15,
        weight_emotion=0.05,
        weight_continuity=0.03,
        weight_cinematic_style=0.02,
    )
    svc = ContextualRetrievalService(cfg)
    ranking = _rank_ctx(
        industry="automotive",
        semantic_anchors=["escape", "humo"],
        scene_text="humo negro del escape",
    )
    weak = _rec("a1", 0.91, text="random abstract gradient broll", nf="HOOK")
    strong = _rec("a2", 0.88, text="tubo de escape vehículo humo negro", nf="PROBLEM")
    req = SearchRequest(query="escape", candidate_pool_size=8, n_results=2)
    out = svc.apply_pipeline([weak, strong], req, ranking, embedder=None)
    assert out[0].clip_id == "a2"


def test_diversity_reorders_duplicate_subcategories() -> None:
    cfg = ContextualRetrievalConfig(
        enabled=True,
        lazy_rerank=False,
        diversity_balance_enabled=True,
        diversity_subcategory_penalty=0.25,
        weight_semantic=0.9,
        weight_global_context=0.02,
        weight_narrative=0.02,
        weight_domain=0.02,
        weight_emotion=0.01,
        weight_continuity=0.015,
        weight_cinematic_style=0.015,
    )
    svc = ContextualRetrievalService(cfg)
    ranking = _rank_ctx(industry="general", semantic_anchors=["broll"])
    req = SearchRequest(query="x", candidate_pool_size=20, n_results=4)
    same_sub = "interior_car"
    recs = [
        _rec("d0", 0.99, text="wide shot interior", sub=same_sub, nf="HOOK"),
        _rec("d1", 0.98, text="detail dash interior", sub=same_sub, nf="HOOK"),
        _rec("d2", 0.97, text="steering interior", sub=same_sub, nf="HOOK"),
        _rec("d3", 0.96, text="exterior mountain landscape epic", sub="nature", nf="HOOK"),
    ]
    out = svc.apply_pipeline(recs, req, ranking, embedder=None)
    # El clip de otra subcategoría sube frente a duplicados fuertemente penalizados.
    assert out[1].clip_id == "d3"


def test_automotive_mismatch_heuristic() -> None:
    bad, good = _automotive_mismatch("wildfire forest fire smoke incendio forestal")
    assert bad is True
    assert good is False
    bad2, good2 = _automotive_mismatch("exhaust smoke motor engine mechanic")
    assert good2 is True


def test_contains_industry_synonym() -> None:
    blob = "mecánico revisa el aceite del motor"
    assert _contains_industry(blob, "automotive") == pytest.approx(1.0)


def test_jaccard_tokens() -> None:
    j = _jaccard_tokens("motor turbo aceite", "aceite motor taller")
    assert j > 0.2


def test_retrieval_signals_dataclass() -> None:
    s = RetrievalSignals(
        semantic_score=0.5,
        global_context_score=0.5,
        narrative_score=0.5,
        domain_score=0.5,
        emotion_score=0.5,
        continuity_score=0.5,
        cinematic_style_score=0.5,
        industry_match=1.0,
        object_match=0.4,
        emotion_match=0.5,
        narrative_match=0.5,
        cinematic_style_match=0.5,
        visual_intent_match=0.5,
        semantic_anchor_overlap=0.4,
        domain_mismatch_penalty=0.0,
    )
    assert s.domain_mismatch_penalty == 0.0


def test_get_contextual_retrieval_service_singleton_config() -> None:
    svc = get_contextual_retrieval_service()
    assert isinstance(svc, ContextualRetrievalService)
    assert svc.cfg.enabled in (True, False)
