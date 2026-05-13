"""Tests Fase 5: reglas de dominio, fragmento Chroma y resolver."""

from __future__ import annotations

from aicos.application.cinematic_metadata.chroma_fragment import chroma_cinematic_fragment
from aicos.application.cinematic_metadata.resolver import CinematicMetadataResolver
from aicos.domain.cinematic_metadata.entities import SourceVideoMetadata
from aicos.domain.cinematic_metadata.rules import (
    fingerprint_visual_embedding,
    resolve_source_video_identifier,
    resolve_visual_cluster_identifier,
)
from aicos.domain.clip_usage.derivations import folder_fallback_hash_for_path
from aicos.models.schemas import Recommendation


def test_resolve_source_prefers_explicit_id() -> None:
    meta = SourceVideoMetadata(source_video_id="SRC-001", master_reel_id="")
    folder = folder_fallback_hash_for_path("/x/a.mp4", "")
    assert resolve_source_video_identifier(meta, folder_fallback_hash=folder) == "SRC-001"


def test_resolve_source_uses_master_when_no_source_id() -> None:
    meta = SourceVideoMetadata(master_reel_id="REEL-A")
    folder = folder_fallback_hash_for_path("/x/a.mp4", "")
    rid = resolve_source_video_identifier(meta, folder_fallback_hash=folder)
    assert rid.startswith("master_reel") is False
    assert len(rid) == 22


def test_visual_cluster_embedding_namespace() -> None:
    v = [0.1, -0.2, 0.3]
    fp = fingerprint_visual_embedding(v, model_tag="t")
    cid = resolve_visual_cluster_identifier(
        explicit_cluster_id=None,
        visual_embedding_fingerprint=fp,
        lexical_cluster_id="lex123",
    )
    assert cid.startswith("vfp:")


def test_chroma_fragment_contains_keys() -> None:
    meta = SourceVideoMetadata(source_video_id="S1", source_video_name="Master A")
    folder = "abc123"
    frag = chroma_cinematic_fragment(
        explicit=meta,
        folder_fallback_hash=folder,
        lexical_visual_cluster_id="lx",
        visual_embedding_vector=None,
        precomputed_visual_fp="fp9",
    )
    assert "cm_source_video_id" in frag
    assert "cm_visual_cluster_id" in frag


def test_resolver_uses_chroma_fields_on_recommendation() -> None:
    rec = Recommendation(
        clip_id="c1",
        clip_path="/lib/p/x.mp4",
        rank=1,
        similarity_score=0.5,
        taxonomy_boost=0.0,
        final_score=0.5,
        cm_source_video_id="OVERRIDE",
        cm_visual_embedding_fp="abc",
    )
    r = CinematicMetadataResolver(None)
    assert r.resolve_source_video_id(rec) == "OVERRIDE"
