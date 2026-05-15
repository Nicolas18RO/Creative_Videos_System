"""Tests Fase 6.3 — embeddings de estilo editorial."""

from __future__ import annotations

from aicos.application.editorial_style_embedding.editorial_style_embedding_service import EditorialStyleEmbeddingService
from aicos.config import EditorialStyleEmbeddingConfig
from aicos.domain.editorial_dataset.entities import (
    CreativeStyleProfile,
    CreativeTimeline,
    EditorialStyleSignals,
    TimelineScene,
)


def _timeline() -> CreativeTimeline:
    scenes = tuple(
        TimelineScene(
            scene_index=i,
            clip_id=f"c{i}",
            start_time=float(i),
            end_time=float(i) + 0.8,
            duration=0.8,
            transition_type="cut",
            narrative_role="hook" if i == 0 else "body",
            motion_intensity=0.6,
            visual_energy=0.55,
            camera_type="macro",
            semantic_tags=("motor",),
            emotion_tags=("tension",),
        )
        for i in range(4)
    )
    sp = CreativeStyleProfile(
        hook_intensity=0.7,
        average_pacing=0.8,
        motion_density=0.5,
        transition_density=0.2,
        narrative_aggressiveness=0.4,
        visual_dynamism=0.55,
        cinematic_style_tags=("macro_heavy",),
    )
    ss = EditorialStyleSignals(
        pacing_score=0.45,
        hook_strength=0.6,
        emotional_curve=(0.5, 0.55, 0.6, 0.58),
        visual_dynamism=0.55,
    )
    return CreativeTimeline(
        creative_id="style_emb_test",
        audio_path="",
        final_video_path="",
        timeline_scenes=scenes,
        style_profile=sp,
        style_signals=ss,
        editorial_patterns=(),
        hook_detection=(),
        pattern_engine_report=None,
    )


def test_style_embedding_structural_dim_and_digest() -> None:
    ec = EditorialStyleEmbeddingConfig(enabled=True, enable_semantic_embedding=False, fusion_mode="structural_only")
    svc = EditorialStyleEmbeddingService(ec, semantic=None)
    emb = svc.embed_timeline(_timeline(), pattern_engine_report=None)
    assert len(emb.structural_vector) == 128
    assert emb.semantic_vector is None
    assert len(emb.fused_vector) == 128
    assert len(emb.digest_sha256) == 64


def test_domain_structural_encoder_deterministic() -> None:
    from aicos.application.editorial_style_embedding.style_structural_source_builder import build_style_structural_source
    from aicos.domain.editorial_style_embedding.structural_vector import structural_vector_from_source

    src = build_style_structural_source(_timeline(), None)
    v1 = structural_vector_from_source(src)
    v2 = structural_vector_from_source(src)
    assert v1 == v2
