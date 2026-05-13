"""Tests unitarios: Clip Usage Intelligence (Fase 4)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from aicos.application.clip_usage.clip_usage_intelligence_service import (
    ClipUsageIntelligenceService,
    get_clip_usage_intelligence_service,
)
from aicos.application.clip_usage.signals_lexical import (
    compute_visual_diversity_signals,
    narrative_concept_overlap_penalty,
)
from aicos.config import ClipUsageIntelligenceConfig
from aicos.domain.clip_usage.derivations import (
    derive_source_video_id,
    derive_visual_cluster_id,
    infer_temporal_shot_bucket,
)
from aicos.models.schemas import (
    ClipUsageRecordSchema,
    GlobalContextSummary,
    Recommendation,
    SearchRequest,
    SearchRankingContext,
    SearchRunContext,
)


def test_derive_source_video_id_stable_per_folder() -> None:
    a = derive_source_video_id("C:/lib/auto/clip1.mp4", "")
    b = derive_source_video_id("C:/lib/auto/clip2.mp4", "")
    c = derive_source_video_id("C:/lib/other/clip1.mp4", "")
    assert a == b
    assert a != c


def test_infer_temporal_shot_bucket() -> None:
    assert infer_temporal_shot_bucket("macro shot of piston") == "closeup"
    assert infer_temporal_shot_bucket("aerial view highway") == "wide"
    assert infer_temporal_shot_bucket("exhaust smoke tailpipe") == "exhaust"


def test_visual_diversity_signals_high_overlap_same_bucket() -> None:
    cur = "motor engine smoke exhaust mechanic"
    ref = "engine smoke motor workshop"
    sig = compute_visual_diversity_signals(cur, ref)
    assert sig.semantic_similarity > 0.2


def test_narrative_overlap_penalty() -> None:
    pen = narrative_concept_overlap_penalty(
        "motor humo escape",
        ["humo motor destruye"],
        scale=0.5,
    )
    assert pen > 0.0


def _rec(
    cid: str,
    fs: float,
    *,
    path: str = "/lib/a/x.mp4",
    sub: str = "auto",
    sem: str = "engine",
) -> Recommendation:
    return Recommendation(
        clip_id=cid,
        clip_path=path,
        rank=1,
        similarity_score=fs,
        taxonomy_boost=0.0,
        final_score=fs,
        narrative_function="PROBLEM",
        clip_subcategory=sub,
        clip_semantic_text=sem,
    )


def test_exact_reuse_heavy_penalty() -> None:
    cfg = ClipUsageIntelligenceConfig(
        enabled=True,
        hard_exclude_exact_reuse=False,
        exact_clip_penalty=0.9,
        diversity_weight=1.0,
        continuity_weight=0.0,
    )
    svc = ClipUsageIntelligenceService(cfg)
    recs = [_rec("c1", 0.99), _rec("c2", 0.5)]
    req = SearchRequest(query="q", used_clip_ids=["c1"])
    ctx = SearchRunContext(source="audio", correlation_id="p1", scene_index=1, clip_usage_records=[])
    out = svc.apply_for_search(recs, req, ctx)
    assert out[0].clip_id == "c2"


def test_hard_exclude_exact_when_alternatives_exist() -> None:
    cfg = ClipUsageIntelligenceConfig(
        enabled=True,
        hard_exclude_exact_reuse=True,
        allow_same_clip=False,
        min_alternatives_for_hard_exclude=2,
        exact_clip_penalty=0.5,
        diversity_weight=0.1,
        continuity_weight=0.0,
    )
    svc = ClipUsageIntelligenceService(cfg)
    recs = [_rec("c1", 0.99), _rec("c2", 0.4), _rec("c3", 0.38)]
    req = SearchRequest(query="q", used_clip_ids=["c1"])
    ctx = SearchRunContext(source="audio", correlation_id="p1", scene_index=2, clip_usage_records=[])
    out = svc.apply_for_search(recs, req, ctx)
    assert all(r.clip_id != "c1" for r in out)


def test_source_penalty_prefers_diverse_origin() -> None:
    cfg = ClipUsageIntelligenceConfig(
        enabled=True,
        hard_exclude_exact_reuse=False,
        same_source_penalty=0.8,
        diversity_weight=1.0,
        continuity_weight=0.0,
        allow_same_source_video=True,
    )
    svc = ClipUsageIntelligenceService(cfg)
    same_path_parent = "/lib/shared/p1.mp4"
    other = "/lib/other/z.mp4"
    cluster_a = derive_visual_cluster_id(
        clip_id="x1", subcategory="s", context="c", semantic_text="unique1", absolute_path=other
    )
    records = [
        ClipUsageRecordSchema(
            clip_id="used",
            source_video_id=derive_source_video_id(same_path_parent, ""),
            visual_cluster_id=cluster_a,
            scene_index=0,
            clip_fingerprint="motor wide shot",
        )
    ]
    recs = [
        _rec("n1", 0.9, path=same_path_parent, sem="oil"),
        _rec("n2", 0.88, path=other, sem="mechanic wrench"),
    ]
    req = SearchRequest(query="q", used_clip_ids=["used"])
    ctx = SearchRunContext(source="audio", correlation_id="p1", scene_index=1, clip_usage_records=records)
    out = svc.apply_for_search(recs, req, ctx)
    assert out[0].clip_id == "n2"


def test_non_audio_context_skips() -> None:
    cfg = ClipUsageIntelligenceConfig(enabled=True)
    svc = ClipUsageIntelligenceService(cfg)
    recs = [_rec("a", 0.5)]
    req = SearchRequest(query="q")
    ctx = SearchRunContext(source="api", correlation_id="p", scene_index=0)
    out = svc.apply_for_search(recs, req, ctx)
    assert out == recs


def test_get_service_handles_bad_config() -> None:
    with patch("aicos.application.clip_usage.clip_usage_intelligence_service.get_config", side_effect=RuntimeError("x")):
        svc = get_clip_usage_intelligence_service()
        assert isinstance(svc, ClipUsageIntelligenceService)
