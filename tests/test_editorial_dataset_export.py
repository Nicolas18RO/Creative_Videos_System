"""Tests de exportación de datasets editoriales."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from aicos.application.editorial_dataset.creative_dataset_export_service import (
    CreativeDatasetExportService,
    timeline_to_dataset_record,
)
from aicos.config import EditorialDatasetConfig
from aicos.domain.editorial_dataset.entities import (
    CreativeStyleProfile,
    CreativeTimeline,
    EditorialStyleSignals,
    TimelineScene,
)
from aicos.infrastructure.editorial_dataset.dataset_file_writer import LocalDatasetFileWriter


def _one_timeline() -> CreativeTimeline:
    scenes = (
        TimelineScene(
            scene_index=0,
            clip_id="a",
            start_time=0.0,
            end_time=1.0,
            duration=1.0,
            transition_type="cut",
            narrative_role="hook",
            motion_intensity=0.6,
            visual_energy=0.7,
            camera_type="macro",
            semantic_tags=("detail",),
            emotion_tags=("tension",),
        ),
    )
    profile = CreativeStyleProfile(
        hook_intensity=0.5,
        average_pacing=1.0,
        motion_density=0.6,
        transition_density=0.1,
        narrative_aggressiveness=0.4,
        visual_dynamism=0.5,
        cinematic_style_tags=("macro_heavy",),
    )
    signals = EditorialStyleSignals(
        pacing_score=0.4,
        hook_strength=0.55,
        emotional_curve=(0.6,),
        visual_dynamism=0.5,
    )
    return CreativeTimeline(
        creative_id="export_c1",
        audio_path="/tmp/a.wav",
        final_video_path="/tmp/v.mp4",
        timeline_scenes=scenes,
        style_profile=profile,
        style_signals=signals,
    )


def test_timeline_to_dataset_record_shape() -> None:
    t = _one_timeline()
    rec = timeline_to_dataset_record(t)
    assert rec["creative_id"] == "export_c1"
    assert "style_profile" in rec and "timeline" in rec
    assert rec["timeline"][0]["clip_id"] == "a"


def test_export_jsonl(tmp_path: Path) -> None:
    cfg = EditorialDatasetConfig(export_jsonl=True)
    writer = LocalDatasetFileWriter()
    svc = CreativeDatasetExportService(cfg=cfg, writer=writer)
    out = tmp_path / "out.jsonl"
    svc.export_jsonl((_one_timeline(),), out)
    lines = out.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    row = json.loads(lines[0])
    assert row["creative_id"] == "export_c1"
    assert "style_profile" in row and "timeline" in row


def test_export_parquet_skips_when_disabled(tmp_path: Path) -> None:
    cfg = EditorialDatasetConfig(export_parquet=False)
    svc = CreativeDatasetExportService(cfg=cfg, writer=LocalDatasetFileWriter())
    svc.export_parquet((_one_timeline(),), tmp_path / "x.parquet")


def test_export_parquet_when_enabled_requires_pyarrow(tmp_path: Path) -> None:
    pa = pytest.importorskip("pyarrow")
    assert pa is not None
    cfg = EditorialDatasetConfig(export_parquet=True)
    svc = CreativeDatasetExportService(cfg=cfg, writer=LocalDatasetFileWriter())
    out = tmp_path / "ds.parquet"
    svc.export_parquet((_one_timeline(),), out)
    assert out.is_file()
