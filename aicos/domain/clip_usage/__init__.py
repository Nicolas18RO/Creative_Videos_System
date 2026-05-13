"""Dominio: inteligencia de uso de clips (no repetición, diversidad cinematográfica)."""

from aicos.domain.clip_usage.entities import ClipReusePolicy, ClipUsageRecord, VisualDiversitySignals
from aicos.domain.clip_usage.enums import ClipUsageType
from aicos.domain.clip_usage.derivations import (
    derive_source_video_id,
    derive_visual_cluster_id,
    infer_temporal_shot_bucket,
)

__all__ = [
    "ClipReusePolicy",
    "ClipUsageRecord",
    "VisualDiversitySignals",
    "ClipUsageType",
    "derive_source_video_id",
    "derive_visual_cluster_id",
    "infer_temporal_shot_bucket",
]
