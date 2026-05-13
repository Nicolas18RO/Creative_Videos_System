"""Tests ranking híbrido multimodal (Fase 5.2)."""

from __future__ import annotations

from aicos.config import MultimodalRetrievalConfig
from aicos.models.schemas import GlobalContextSummary, Recommendation, SearchRequest, SearchRunContext
from aicos.modules.multimodal_hybrid_retrieval import apply_multimodal_hybrid_to_recommendations


def _rec(
    *,
    clip_id: str,
    final: float,
    fp: str | None,
    cluster: str | None,
) -> Recommendation:
    return Recommendation(
        clip_id=clip_id,
        clip_path="/x.mp4",
        rank=1,
        similarity_score=0.5,
        taxonomy_boost=0.0,
        final_score=final,
        cm_visual_embedding_fp=fp,
        cm_visual_cluster_id=cluster,
        clip_semantic_text="smoke motor",
    )


def test_hybrid_boosts_when_fingerprint_matches() -> None:
    req = SearchRequest(
        query="smoke",
        reference_visual_fingerprint="deadbeef" * 2,
        reference_visual_cluster_id="clusterA",
    )
    cfg = MultimodalRetrievalConfig(enabled=True, enable_visual_similarity=True, visual_similarity_weight=0.5)
    recs = [
        _rec(clip_id="a", final=0.5, fp="deadbeef" * 2, cluster="clusterA"),
        _rec(clip_id="b", final=0.55, fp="00000000" * 2, cluster="other"),
    ]
    out = apply_multimodal_hybrid_to_recommendations(recs, req, retrieval_cfg=cfg, context=None)
    assert out[0].clip_id == "a"
    assert out[0].visual_similarity_score >= out[1].visual_similarity_score


def test_hybrid_disabled_returns_same_order() -> None:
    req = SearchRequest(query="x", reference_visual_fingerprint="abc")
    cfg = MultimodalRetrievalConfig(enabled=False, enable_visual_similarity=True)
    recs = [_rec(clip_id="a", final=0.4, fp="abc", cluster=None)]
    out = apply_multimodal_hybrid_to_recommendations(recs, req, retrieval_cfg=cfg)
    assert out == recs


def test_hybrid_continuity_from_global_context() -> None:
    req = SearchRequest(query="x")
    cfg = MultimodalRetrievalConfig(enabled=True, enable_visual_similarity=True, visual_similarity_weight=0.1)
    ctx = SearchRunContext(
        global_context=GlobalContextSummary(visual_style="warm_grade"),
    )
    recs = [
        _rec(clip_id="a", final=0.5, fp=None, cluster=None).model_copy(
            update={"clip_semantic_text": "warm_grade cinematic"}
        ),
    ]
    out = apply_multimodal_hybrid_to_recommendations(recs, req, retrieval_cfg=cfg, context=ctx)
    assert out[0].final_score >= recs[0].final_score
