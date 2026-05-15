"""Entidades inmutables de feedback editorial humano (sin ORM)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class EditorialHumanFeedbackEvent:
    """Una señal explícita de preferencia o corrección editorial (auditable)."""

    id: str
    created_at: datetime
    event_kind: str
    reward: float
    creative_id: str | None
    clip_id: str | None
    replaced_clip_id: str | None
    scene_index: int | None
    narrative_function: str | None
    transition_type: str | None
    query_fingerprint: str | None
