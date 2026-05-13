"""Integración: search_service invoca Clip Usage tras Narrative Memory."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from aicos.models.schemas import Recommendation, SearchRequest, SearchRunContext
from aicos.services import search_service


def _rec(cid: str, score: float) -> Recommendation:
    return Recommendation(
        clip_id=cid,
        clip_path=f"/L/{cid}.mp4",
        rank=1,
        similarity_score=score,
        taxonomy_boost=0.0,
        final_score=score,
        narrative_function="PROBLEM",
        clip_subcategory="auto",
        clip_semantic_text=f"semantic {cid}",
    )


def test_search_pipeline_calls_clip_usage_after_nm() -> None:
    recs = [_rec("a", 0.9), _rec("b", 0.89)]
    ctx = SearchRunContext(
        source="audio",
        correlation_id="corr-1",
        scene_index=1,
        clip_usage_records=[],
    )
    req = SearchRequest(query="motor", used_clip_ids=["a"], n_results=2, candidate_pool_size=10)

    def _cfg():
        m = MagicMock()
        m.search.gap_threshold = 0.0
        m.contextual_retrieval.enabled = False
        m.narrative_memory.enabled = True
        m.clip_usage_intelligence.enabled = True
        m.clip_usage_intelligence.persist_history = False
        return m

    with patch("aicos.modules.clip_recommender.build_ranked_recommendations", return_value=list(recs)):
        with patch("aicos.services.search_service._safe_get_app_config", side_effect=_cfg):
            with patch("aicos.services.search_service.record_audio_segment_search"):
                with patch("aicos.services.search_service.compute_intelligence_boosts", return_value={}):
                    with patch("aicos.services.search_service.compute_audio_session_penalties", return_value={}):
                        with patch(
                            "aicos.application.cinematic.narrative_memory_service.get_narrative_memory_service"
                        ) as gnms:
                            gnms.return_value.apply_for_search.side_effect = lambda _s, r, _q, _c: r
                            with patch(
                                "aicos.application.clip_usage.clip_usage_intelligence_service.get_clip_usage_intelligence_service"
                            ) as gcui:
                                mock_svc = MagicMock()
                                mock_svc.apply_for_search.side_effect = lambda r, _q, _c, *_a: r
                                gcui.return_value = mock_svc
                                session = MagicMock()
                                out = search_service.run_search(
                                    session,
                                    req,
                                    MagicMock(),
                                    MagicMock(),
                                    context=ctx,
                                )
                                mock_svc.apply_for_search.assert_called_once()
                                assert len(out.results) >= 1
                                assert out.results[0].clip_id in ("a", "b")
