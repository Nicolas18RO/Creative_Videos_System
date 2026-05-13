"""Entidades puras de metadata editorial (Fase 5.3)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class EditorialMetadataRecord:
    """Vista fusionada: clip + cinematográfico + capa editorial."""

    clip_id: str
    source_video_id: str
    master_reel_id: str
    editorial_tags: str
    editorial_notes: str
    narrative_role: str
    emotion_profile: str
    visual_style: str
    cinematic_style: str
    visual_cluster_id: str
    cluster_override: str
    pacing_type: str
    shot_type: str
    quality_score: float | None
    cinematic_score: float | None
    reviewed: bool
    reviewed_by: str
    reviewed_at: datetime | None
    created_at: datetime | None
    updated_at: datetime | None


@dataclass(frozen=True, slots=True)
class EditorialCorrection:
    """Auditoría de un cambio de campo."""

    field_name: str
    previous_value: str
    corrected_value: str
    correction_reason: str
    corrected_by: str
    timestamp: datetime


@dataclass(frozen=True, slots=True)
class EditorialFeedbackSignal:
    """Señal humana agregada por clip."""

    clip_id: str
    usefulness_score: float
    continuity_score: float
    diversity_score: float
    narrative_quality: float
    visual_quality: float
    human_feedback: str
