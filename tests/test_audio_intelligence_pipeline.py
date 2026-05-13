"""Integración ligera: audio_intelligence + config + persistencia narrativa."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from aicos.models.schemas import (
    GlobalContextSummary,
    Recommendation,
    Scene,
    SearchResponse,
    SearchRankingContext,
    SearchRunContext,
)
from aicos.services import audio_intelligence_service as ais


def _scene() -> Scene:
    return Scene(
        scene_id="s0",
        scene_index=0,
        start_ms=0,
        end_ms=800,
        duration_ms=800,
        text="y humo",
        concept="humo escape motor",
        narrative_function="PROBLEM",
        is_hook=False,
    )


def _rec() -> Recommendation:
    return Recommendation(
        clip_id="clip-a",
        clip_path="/x.mp4",
        rank=1,
        similarity_score=0.9,
        taxonomy_boost=0.0,
        final_score=0.9,
        narrative_function="PROBLEM",
        clip_subcategory="auto",
        clip_semantic_text="motor exhaust smoke mechanic",
    )


def test_run_analyze_scene_search_no_nameerror_with_narrative_enabled() -> None:
    """Regresión: ``get_config`` debe estar definido al evaluar narrative_memory."""
    g = GlobalContextSummary(
        topic="aditivos para motor",
        industry="automotive",
        dominant_emotion="concern",
        narrative_arc="problem_solution",
        visual_style="cinematic",
        semantic_anchors=["motor", "humo", "daño"],
    )
    resp = SearchResponse(results=[_rec()], is_gap=False, query_fingerprint="fp")
    session = MagicMock()
    emb = MagicMock()
    store = MagicMock()

    captured_ctx: dict = {}

    def _capture_run_search(sess, req, e, st, context=None):
        captured_ctx["ctx"] = context
        return resp

    with patch.object(ais.search_service, "run_search", side_effect=_capture_run_search):
        with patch.object(ais, "get_config") as mock_gc:
            cfg = MagicMock()
            cfg.narrative_memory.enabled = True
            mock_gc.return_value = cfg
            with patch(
                "aicos.application.cinematic.narrative_memory_service.get_narrative_memory_service"
            ) as gnms:
                gnms.return_value.persist_after_top_selection = MagicMock()
                out = ais.run_analyze_scene_search(
                    session,
                    scene=_scene(),
                    embedder=emb,
                    store=store,
                    used_clip_ids=[],
                    correlation_id="corr-test-1",
                    scene_index=3,
                    enable_intelligence=True,
                    global_context=g,
                    prior_scene_concepts=["motor turbo"],
                )
                assert out.results[0].clip_id == "clip-a"
                gnms.return_value.persist_after_top_selection.assert_called_once()
                ctx = captured_ctx["ctx"]
                assert isinstance(ctx, SearchRunContext)
                assert ctx.global_context is not None
                assert ctx.ranking_context is not None
                assert ctx.ranking_context.industry == "automotive"
                assert ctx.scene_index == 3


def test_global_domain_propagates_for_ambiguous_scene_text() -> None:
    """Escenas cortas no deben perder el dominio global en ``SearchRankingContext``."""
    g = GlobalContextSummary(
        industry="automotive",
        topic="lubricantes",
        dominant_emotion="neutral",
        narrative_arc="linear",
        visual_style="commercial",
        semantic_anchors=["aceite", "motor"],
    )
    scene = Scene(
        scene_id="s2",
        scene_index=2,
        start_ms=0,
        end_ms=400,
        duration_ms=400,
        text="lo está destruyendo",
        concept="daño",
        narrative_function="PROBLEM",
        is_hook=False,
    )
    rk = SearchRankingContext(
        industry=g.industry,
        topic=g.topic,
        dominant_emotion=g.dominant_emotion,
        semantic_anchors=list(g.semantic_anchors),
        narrative_arc=g.narrative_arc,
        visual_style=g.visual_style,
        content_intent=g.content_intent,
        scene_text=scene.text,
        scene_concept=scene.concept,
        narrative_function=scene.narrative_function,
        previous_selected_clip_ids=[],
        prior_scene_concepts=[],
    )
    assert rk.industry == "automotive"
    assert "motor" in rk.semantic_anchors


@pytest.mark.parametrize(
    "nm_enabled",
    [True, False],
)
def test_persist_skipped_when_narrative_disabled(nm_enabled: bool) -> None:
    resp = SearchResponse(results=[_rec()], is_gap=False, query_fingerprint=None)
    session = MagicMock()
    with patch.object(ais.search_service, "run_search", return_value=resp):
        with patch.object(ais, "get_config") as mock_gc:
            cfg = MagicMock()
            cfg.narrative_memory.enabled = nm_enabled
            mock_gc.return_value = cfg
            with patch(
                "aicos.application.cinematic.narrative_memory_service.get_narrative_memory_service"
            ) as gnms:
                gnms.return_value.persist_after_top_selection = MagicMock()
                ais.run_analyze_scene_search(
                    session,
                    scene=_scene(),
                    embedder=MagicMock(),
                    store=MagicMock(),
                    used_clip_ids=[],
                    correlation_id="c2",
                    scene_index=0,
                    enable_intelligence=True,
                    global_context=GlobalContextSummary(industry="general"),
                )
                if nm_enabled:
                    gnms.return_value.persist_after_top_selection.assert_called_once()
                else:
                    gnms.return_value.persist_after_top_selection.assert_not_called()
