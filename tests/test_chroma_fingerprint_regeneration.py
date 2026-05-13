"""Tests regeneración Chroma multimodal (mocks, sin Chroma real)."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from aicos.application.multimodal_retrieval.chroma_fingerprint_regeneration_service import (
    ChromaFingerprintRegenerationService,
)
from aicos.config import CinematicMetadataConfig, MultimodalRetrievalConfig
from aicos.domain.multimodal_retrieval.entities import (
    ChromaClipFacet,
    ChromaFingerprintPayload,
    MultimodalRegenWorkUnit,
    VisualFingerprintRecord,
)
from aicos.services.chroma_multimodal_metadata import build_multimodal_chroma_metadata


def _facet() -> ChromaClipFacet:
    return ChromaClipFacet(
        clip_id="c1",
        filename="a.mp4",
        relative_path="a.mp4",
        absolute_path="/v/a.mp4",
        gender=None,
        narrative_function="BROLL",
        subcategory="motors",
        context=None,
        semantic_text="motor humo",
        naming_compliant=True,
        thumbnail_path=None,
        source_video_id="src1",
        source_video_name=None,
        master_reel_id="mr1",
        shooting_session_id=None,
        camera_id="cam1",
        production_group="pg1",
        visual_collection="col1",
        creation_date=None,
        location_tag="loc1",
        visual_cluster_id_explicit="clu1",
    )


def _visual() -> VisualFingerprintRecord:
    return VisualFingerprintRecord(
        clip_id="c1",
        fingerprint="a" * 16,
        embedding_model="openclip/ViT-B-32/laion2b_s34b_b79k",
        embedding_dimension=2,
        created_at=datetime.now(timezone.utc),
        source_video_id="src1",
        visual_cluster_id="clu1",
    )


def test_build_multimodal_chroma_metadata_includes_cm_keys() -> None:
    meta = build_multimodal_chroma_metadata(facet=_facet(), visual=_visual(), continuity=None)
    assert meta.get("cm_visual_embedding_fp")
    assert meta.get("cm_source_video_id") == "src1"
    assert meta.get("cm_master_reel_id") == "mr1"
    assert meta.get("cm_camera_id") == "cam1"
    assert meta.get("cm_production_group") == "pg1"
    assert meta.get("cm_visual_collection") == "col1"
    assert meta.get("cm_location_tag") == "loc1"


def test_regeneration_service_calls_writer() -> None:
    unit = MultimodalRegenWorkUnit(
        visual=_visual(),
        facet=_facet(),
        embedding_vector=(0.1, 0.2),
    )
    reader = MagicMock()
    reader.fetch_work_units.return_value = [unit]
    writer = MagicMock()
    svc = ChromaFingerprintRegenerationService(
        batch_reader=reader,
        writer=writer,
        retrieval_cfg=MultimodalRetrievalConfig(strict_model_match=False),
        cinematic_cfg=CinematicMetadataConfig(
            openclip_model="ViT-B-32",
            openclip_pretrained="laion2b_s34b_b79k",
        ),
    )
    stats, last = svc.regenerate_batch(MagicMock(), after_clip_id=None, limit=10)
    writer.upsert_multimodal.assert_called_once()
    args, kwargs = writer.upsert_multimodal.call_args
    payloads: list[ChromaFingerprintPayload] = args[1]
    assert len(payloads) == 1
    assert payloads[0].chroma_id == "c1"
    assert stats.indexed == 1
    assert last == "c1"


def test_regeneration_skips_bad_embedding_dimension() -> None:
    unit = MultimodalRegenWorkUnit(
        visual=_visual(),
        facet=_facet(),
        embedding_vector=(0.1,),  # mismatch dim 2
    )
    reader = MagicMock()
    reader.fetch_work_units.return_value = [unit]
    writer = MagicMock()
    svc = ChromaFingerprintRegenerationService(
        batch_reader=reader,
        writer=writer,
        retrieval_cfg=MultimodalRetrievalConfig(),
        cinematic_cfg=CinematicMetadataConfig(),
    )
    stats, _last = svc.regenerate_batch(MagicMock(), after_clip_id=None, limit=10)
    writer.upsert_multimodal.assert_not_called()
    assert stats.indexed == 0
    assert stats.failed >= 1


@pytest.mark.parametrize(
    "a,b,expect_one",
    [
        ("abcd1234", "abcd9999", True),
        ("", "abcd", False),
    ],
)
def test_hybrid_prefix_similarity_partial(a: str, b: str, expect_one: bool) -> None:
    from aicos.domain.multimodal_retrieval.hybrid_scoring import compute_visual_similarity_components

    _fp, _cl, blended = compute_visual_similarity_components(
        reference_fingerprint=a,
        reference_cluster_id="",
        clip_fingerprint=b,
        clip_cluster_id=None,
    )
    if expect_one:
        assert blended > 0.0
    else:
        assert blended == 0.0
