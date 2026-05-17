"""Entidades de revisión editorial por escena."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class EditorialSceneReviewState:
    scene_id: str
    status: str
    reviewed_at: datetime | None
    reviewer: str
    correction_reason: str
    merged_into_scene_id: str | None
    confidence_override: float | None
    notes: str


@dataclass(frozen=True, slots=True)
class EditorialSceneMergeRecord:
    source_scene_a: str
    source_scene_b: str
    resulting_scene_id: str
    session_id: str
    created_at: datetime
