"""Tests unitarios del servicio editorial (mocks)."""

from __future__ import annotations

from dataclasses import replace
from unittest.mock import MagicMock

import pytest

from aicos.application.editorial_metadata.editorial_metadata_service import EditorialMetadataService
from aicos.config import EditorialMetadataConfig
from aicos.domain.editorial_metadata.entities import EditorialMetadataRecord
from aicos.domain.editorial_metadata.rules import (
    apply_editorial_override,
    normalize_editorial_tags,
    validate_editorial_cluster,
)


def test_normalize_editorial_tags_dedup() -> None:
    assert normalize_editorial_tags("A,b, a") == "a,b"


def test_apply_editorial_override() -> None:
    assert apply_editorial_override(auto_cluster="lex1", cluster_override="macro") == "macro"
    assert apply_editorial_override(auto_cluster="lex1", cluster_override=None) == "lex1"


def test_validate_cluster() -> None:
    assert validate_editorial_cluster("ok_cluster-1")[0] is True
    assert validate_editorial_cluster("bad space")[0] is False


def test_patch_clip_persists() -> None:
    dom = EditorialMetadataRecord(
        clip_id="c1",
        source_video_id="",
        master_reel_id="",
        editorial_tags="",
        editorial_notes="",
        narrative_role="",
        emotion_profile="",
        visual_style="",
        cinematic_style="",
        visual_cluster_id="x",
        cluster_override="",
        pacing_type="",
        shot_type="",
        quality_score=None,
        cinematic_score=None,
        reviewed=False,
        reviewed_by="",
        reviewed_at=None,
        created_at=None,
        updated_at=None,
    )
    updated = replace(dom, quality_score=0.9)
    read = MagicMock()
    read.get_by_clip_id.side_effect = [dom, updated]
    write = MagicMock()
    cfg = EditorialMetadataConfig(allow_editorial_overrides=True)
    svc = EditorialMetadataService(read_port=read, write_port=write, cfg=cfg)
    session = MagicMock()
    out = svc.patch_clip(
        session,
        clip_id="c1",
        fields={"quality_score": 0.9},
        corrected_by="tester",
        correction_reason="qa",
    )
    write.patch.assert_called_once()
    assert out.quality_score == 0.9


def test_patch_clip_not_found() -> None:
    read = MagicMock()
    read.get_by_clip_id.return_value = None
    svc = EditorialMetadataService(
        read_port=read,
        write_port=MagicMock(),
        cfg=EditorialMetadataConfig(),
    )
    with pytest.raises(LookupError):
        svc.patch_clip(
            MagicMock(),
            clip_id="missing",
            fields={"editorial_tags": "x"},
            corrected_by="a",
            correction_reason="b",
        )
