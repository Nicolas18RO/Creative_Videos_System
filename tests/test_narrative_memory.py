"""Tests Narrative Memory System (Fase 3)."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from aicos.application.cinematic.narrative_memory_service import (
    NarrativeMemoryService,
    advance_state_after_selection,
    initial_memory_state,
    load_state_for_scene,
)
from aicos.config import NarrativeMemoryConfig
from aicos.database.db import Base
from aicos.models.schemas import (
    GlobalContextSummary,
    Recommendation,
    Scene,
    SearchRankingContext,
    SearchRequest,
    SearchRunContext,
)
from aicos.services import narrative_memory_repository as nm_repo


def _memory_session() -> Session:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)()


def _rec(clip_id: str, sim: float, text: str, *, sub: str = "x", final: float | None = None) -> Recommendation:
    fs = final if final is not None else sim
    return Recommendation(
        clip_id=clip_id,
        clip_path=f"/{clip_id}.mp4",
        rank=1,
        similarity_score=sim,
        taxonomy_boost=0.0,
        final_score=fs,
        narrative_function="PROBLEM",
        clip_subcategory=sub,
        clip_context="",
        clip_semantic_text=text,
    )


def test_initial_automotive_cinematic_lock() -> None:
    g = GlobalContextSummary(
        industry="automotive",
        visual_style="cinematic_dark",
        narrative_arc="problem_solution",
        dominant_emotion="concern",
    )
    st = initial_memory_state("cid-1", g)
    assert st.industry_lock_active is True
    assert "industry_lock_automotive_cinematic" in st.continuity_constraints


def test_arc_cta_releases_lock_in_advance() -> None:
    cfg = NarrativeMemoryConfig(enabled=True, window_size=4)
    g = GlobalContextSummary(industry="automotive", visual_style="cinematic", narrative_arc="ps")
    prior = initial_memory_state("c", g)
    top = _rec("a1", 0.9, "motor cinematic", sub="auto")
    scene = Scene(
        scene_id="s1",
        scene_index=0,
        start_ms=0,
        end_ms=1000,
        duration_ms=1000,
        text="x",
        concept="motor",
        narrative_function="CTA",
        is_hook=False,
    )
    new_st = advance_state_after_selection(cfg, prior, scene_index=0, scene=scene, top=top, global_ctx=g)
    assert new_st.industry_lock_active is False


def test_sliding_window_respects_window_size() -> None:
    cfg = NarrativeMemoryConfig(window_size=2)
    g = GlobalContextSummary(industry="general", visual_style="clean", narrative_arc="linear")
    st = initial_memory_state("w", g)
    for i in range(4):
        top = _rec(f"c{i}", 0.8, f"clip {i}", sub="s")
        scene = Scene(
            scene_id=f"id{i}",
            scene_index=i,
            start_ms=0,
            end_ms=500,
            duration_ms=500,
            text="t",
            concept="c",
            narrative_function="HOOK",
            is_hook=True,
        )
        st = advance_state_after_selection(cfg, st, scene_index=i, scene=scene, top=top, global_ctx=g)
    assert len(st.sliding_window) == 2
    assert st.sliding_window[-1].clip_id == "c3"


def test_industry_lock_penalizes_office_clip() -> None:
    cfg = NarrativeMemoryConfig(
        enabled=True,
        window_size=5,
        continuity_weight=0.05,
        diversity_weight=0.02,
        industry_lock_strength=0.75,
    )
    svc = NarrativeMemoryService(cfg)
    sess = _memory_session()
    cid = str(uuid.uuid4())
    g = GlobalContextSummary(industry="automotive", visual_style="cinematic_commercial", narrative_arc="p")
    ranking = SearchRankingContext(
        industry="automotive",
        narrative_function="PROBLEM",
        scene_text="daño al motor",
        dominant_emotion="concern",
    )
    ctx = SearchRunContext(
        source="audio",
        correlation_id=cid,
        scene_index=0,
        global_context=g,
        ranking_context=ranking,
    )
    office = _rec("o1", 0.95, "corporate office desk meeting reunion", sub="office", final=0.95)
    motor = _rec("m1", 0.94, "motor cinematic mechanic garage automotive", sub="repair", final=0.94)
    req = SearchRequest(query="motor", candidate_pool_size=10, n_results=2)
    out = svc.apply_for_search(sess, [office, motor], req, ctx)
    assert out[0].clip_id == "m1"


def test_cta_scene_allows_incompatible_higher_score() -> None:
    cfg = NarrativeMemoryConfig(
        enabled=True,
        continuity_weight=0.05,
        diversity_weight=0.02,
        industry_lock_strength=0.8,
    )
    svc = NarrativeMemoryService(cfg)
    sess = _memory_session()
    cid = str(uuid.uuid4())
    g = GlobalContextSummary(industry="automotive", visual_style="cinematic", narrative_arc="p")
    ranking = SearchRankingContext(
        industry="automotive",
        narrative_function="CTA",
        scene_text="compra ahora",
    )
    ctx = SearchRunContext(
        source="audio",
        correlation_id=cid,
        scene_index=0,
        global_context=g,
        ranking_context=ranking,
    )
    lifestyle = _rec("l1", 0.96, "lifestyle morning routine kitchen bright", sub="life", final=0.96)
    auto = _rec("a1", 0.90, "coche premium showroom", sub="auto", final=0.90)
    req = SearchRequest(query="cta", candidate_pool_size=5, n_results=2)
    out = svc.apply_for_search(sess, [lifestyle, auto], req, ctx)
    assert out[0].clip_id == "l1"


def test_persistence_snapshot_roundtrip() -> None:
    sess = _memory_session()
    cid = "sess-99"
    g = GlobalContextSummary(industry="beauty", visual_style="soft", narrative_arc="linear")
    st = initial_memory_state(cid, g)
    nm_repo.save_state_snapshot(sess, cid, 0, st.model_dump())
    payload = nm_repo.load_snapshot_by_scene_index(sess, cid, 0)
    assert payload is not None
    assert payload["dominant_industry"] == "beauty"


def test_diversity_penalizes_repeat_clip_id() -> None:
    cfg = NarrativeMemoryConfig(
        enabled=True,
        continuity_weight=0.01,
        diversity_weight=0.4,
        industry_lock_strength=0.5,
        max_repeat_clip_penalty=0.5,
    )
    svc = NarrativeMemoryService(cfg)
    sess = _memory_session()
    cid = str(uuid.uuid4())
    g = GlobalContextSummary(industry="general", visual_style="docu", narrative_arc="linear")
    prior = initial_memory_state(cid, g).model_copy(update={"previous_selected_clips": ["dup"]})
    nm_repo.save_state_snapshot(sess, cid, 0, prior.model_dump())
    ranking = SearchRankingContext(narrative_function="HOOK")
    ctx = SearchRunContext(
        source="audio",
        correlation_id=cid,
        scene_index=1,
        global_context=g,
        ranking_context=ranking,
    )
    dup = _rec("dup", 0.99, "broll abstract", sub="b", final=0.99)
    fresh = _rec("new", 0.88, "broll nature landscape", sub="nature", final=0.88)
    req = SearchRequest(query="x", candidate_pool_size=5, n_results=2)
    out = svc.apply_for_search(sess, [dup, fresh], req, ctx)
    assert out[0].clip_id == "new"


def test_visual_consistency_warm_palette() -> None:
    cfg = NarrativeMemoryConfig(enabled=True, continuity_weight=0.35, diversity_weight=0.02, industry_lock_strength=0.5)
    svc = NarrativeMemoryService(cfg)
    sess = _memory_session()
    cid = str(uuid.uuid4())
    g = GlobalContextSummary(industry="general", visual_style="warm", narrative_arc="linear")
    st0 = initial_memory_state(cid, g)
    top0 = _rec("w0", 0.9, "golden hour warm sepia portrait", sub="p")
    scene0 = Scene(
        scene_id="s0",
        scene_index=0,
        start_ms=0,
        end_ms=500,
        duration_ms=500,
        text="t",
        concept="c",
        narrative_function="HOOK",
        is_hook=True,
    )
    st1 = advance_state_after_selection(cfg, st0, scene_index=0, scene=scene0, top=top0, global_ctx=g)
    nm_repo.save_state_snapshot(sess, cid, 0, st1.model_dump())
    ranking = SearchRankingContext(narrative_function="BENEFIT")
    ctx = SearchRunContext(
        source="audio",
        correlation_id=cid,
        scene_index=1,
        global_context=g,
        ranking_context=ranking,
    )
    warm = _rec("w1", 0.85, "warm golden sunset skin glow", sub="a", final=0.85)
    cool = _rec("w2", 0.86, "cold blue cyan sci fi tech", sub="b", final=0.86)
    req = SearchRequest(query="q", candidate_pool_size=5, n_results=2)
    out = svc.apply_for_search(sess, [cool, warm], req, ctx)
    assert out[0].clip_id == "w1"


def test_load_state_merges_ranking_previous_clips() -> None:
    sess = _memory_session()
    cid = "merge-1"
    ranking = SearchRankingContext(previous_selected_clip_ids=["x1", "x2"])
    st = load_state_for_scene(sess, cid, 0, None, ranking)
    assert st.previous_selected_clips == ["x1", "x2"]


def test_persist_after_top_selection_writes_snapshot() -> None:
    sess = _memory_session()
    cid = "persist-1"
    cfg = NarrativeMemoryConfig(enabled=True, window_size=5)
    svc = NarrativeMemoryService(cfg)
    g = GlobalContextSummary(industry="general", visual_style="clean", narrative_arc="linear")
    top = _rec("c1", 0.9, "wide establishing shot outdoor", sub="est")
    scene = Scene(
        scene_id="s0",
        scene_index=0,
        start_ms=0,
        end_ms=500,
        duration_ms=500,
        text="t",
        concept="intro",
        narrative_function="HOOK",
        is_hook=True,
    )
    ranking = SearchRankingContext(narrative_function="HOOK")
    svc.persist_after_top_selection(
        sess,
        correlation_id=cid,
        scene_index=0,
        top=top,
        scene=scene,
        global_ctx=g,
        ranking=ranking,
    )
    sess.commit()
    row = nm_repo.load_snapshot_by_scene_index(sess, cid, 0)
    assert row is not None
    assert "c1" in row.get("previous_selected_clips", [])
