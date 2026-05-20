"""Entidades de lectura del registro de sesiones editoriales."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class EditorialRegistrySession:
    """Vista de sesión para el registry (committed, en progreso o fallida)."""

    session_id: str
    creative_id: str
    creative_label: str
    project_label: str
    product_category: str
    status: str
    committed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    scene_count: int
    duration_seconds: float
    has_feedback: bool
    has_timeline: bool
    notes: str
    corrections_count: int


# Alias semántico para documentación / consumidores que hablan de «committed»
EditorialCommittedSession = EditorialRegistrySession


@dataclass(frozen=True, slots=True)
class EditorialRegistrySummary:
    total: int
    committed: int
    awaiting_human: int
    analyzing: int
    failed: int
    draft: int
    ready: int
    with_timeline: int
    with_feedback: int
