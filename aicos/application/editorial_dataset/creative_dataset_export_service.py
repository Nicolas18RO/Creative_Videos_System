"""Exportación de datasets editoriales (JSON / JSONL / Parquet opcional)."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterator

from aicos.application.editorial_dataset import logging_utils
from aicos.application.editorial_dataset.ports import DatasetFileWritePort
from aicos.config import EditorialDatasetConfig
from aicos.domain.editorial_dataset.entities import CreativeTimeline, TimelineScene


def _scene_to_jsonable(s: TimelineScene) -> dict[str, Any]:
    d = asdict(s)
    d["semantic_tags"] = list(s.semantic_tags)
    d["emotion_tags"] = list(s.emotion_tags)
    return d


def timeline_to_dataset_record(t: CreativeTimeline) -> dict[str, Any]:
    from aicos.application.editorial_pattern_engine.serialization import report_to_jsonable

    out: dict[str, Any] = {
        "creative_id": t.creative_id,
        "dataset_version": t.dataset_version,
        "audio_path": t.audio_path,
        "final_video_path": t.final_video_path,
        "style_profile": asdict(t.style_profile),
        "style_signals": {
            "pacing_score": t.style_signals.pacing_score,
            "hook_strength": t.style_signals.hook_strength,
            "emotional_curve": list(t.style_signals.emotional_curve),
            "visual_dynamism": t.style_signals.visual_dynamism,
        },
        "timeline": [_scene_to_jsonable(s) for s in t.timeline_scenes],
        "editorial_patterns": [asdict(p) for p in t.editorial_patterns],
        "hook_detection": [asdict(h) for h in t.hook_detection],
    }
    if t.pattern_engine_report is not None:
        out["pattern_engine_report"] = report_to_jsonable(t.pattern_engine_report)
    if t.style_embedding is not None:
        se = t.style_embedding
        out["style_embedding"] = {
            "digest_sha256": se.digest_sha256,
            "structural_dim": len(se.structural_vector),
            "semantic_dim": len(se.semantic_vector) if se.semantic_vector else 0,
            "fused_dim": len(se.fused_vector),
            "fusion_mode": se.fusion_mode,
            "structural_model": se.structural_model_tag,
            "semantic_model": se.semantic_model_tag,
        }
    return out


class CreativeDatasetExportService:
    def __init__(self, *, cfg: EditorialDatasetConfig, writer: DatasetFileWritePort) -> None:
        self._cfg = cfg
        self._writer = writer

    def export_json(self, timeline: CreativeTimeline, path: Path) -> None:
        payload = timeline_to_dataset_record(timeline)
        self._writer.write_text(path, json.dumps(payload, ensure_ascii=False, indent=2))
        logging_utils.log_editorial_dataset("export_json path=%s", path)

    def export_jsonl(self, timelines: tuple[CreativeTimeline, ...], path: Path) -> None:
        if not self._cfg.export_jsonl:
            logging_utils.log_editorial_dataset("export_jsonl_skipped_disabled")
            return
        lines = []
        for t in timelines:
            rec = {
                "creative_id": t.creative_id,
                "style_profile": asdict(t.style_profile),
                "timeline": [_scene_to_jsonable(s) for s in t.timeline_scenes],
            }
            lines.append(json.dumps(rec, ensure_ascii=False))
        self._writer.write_text(path, "\n".join(lines) + ("\n" if lines else ""))
        logging_utils.log_editorial_dataset("export_jsonl rows=%s path=%s", len(timelines), path)

    def iter_jsonl_lines(self, timelines: tuple[CreativeTimeline, ...]) -> Iterator[str]:
        for t in timelines:
            rec = {
                "creative_id": t.creative_id,
                "style_profile": asdict(t.style_profile),
                "timeline": [_scene_to_jsonable(s) for s in t.timeline_scenes],
            }
            yield json.dumps(rec, ensure_ascii=False)

    def export_parquet(self, timelines: tuple[CreativeTimeline, ...], path: Path) -> None:
        if not self._cfg.export_parquet:
            logging_utils.log_editorial_dataset("export_parquet_skipped_disabled")
            return
        try:
            import pyarrow as pa
            import pyarrow.parquet as pq
        except ImportError as e:
            raise RuntimeError(
                "export_parquet requiere pyarrow instalado (pip install pyarrow)"
            ) from e
        rows = [timeline_to_dataset_record(t) for t in timelines]
        table = pa.Table.from_pylist(rows)
        buf = Path(path)
        pq.write_table(table, buf)
        logging_utils.log_editorial_dataset("export_parquet rows=%s path=%s", len(rows), path)
