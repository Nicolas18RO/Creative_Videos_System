"""Entidades puras del workspace de entrenamiento editorial (Fase 6.7)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


class EditorialTrainingSessionStatus:
    """Estados del ciclo de vida de una sesión de entrenamiento."""

    DRAFT = "draft"
    ANALYZING = "analyzing"
    READY = "ready"
    AWAITING_HUMAN = "awaiting_human"
    COMMITTED = "committed"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class EditorialTrainingCorrectionItem:
    """Una decisión humana registrable (se mapea a feedback 6.6 y auditoría)."""

    event_kind: str
    reward: float
    clip_id: str | None = None
    replaced_clip_id: str | None = None
    scene_index: int | None = None
    narrative_function: str | None = None
    transition_type: str | None = None


@dataclass(frozen=True, slots=True)
class EditorialTrainingSession:
    """Sesión de trabajo: creativo + rutas de medios + estado + correcciones acumuladas."""

    session_id: str
    creative_id: str
    project_id: str | None
    status: str
    final_video_path: str
    audio_path: str
    corrections: tuple[EditorialTrainingCorrectionItem, ...]
    created_at: datetime
    updated_at: datetime
    project_label: str = ""
    creative_label: str = ""
    product_category: str = ""
    notes: str = ""


@dataclass(frozen=True, slots=True)
class EditorialTimelineAdjustment:
    """Ajuste humano de timing (Fase 6.8); conserva detección automática original."""

    session_id: str
    scene_index: int
    auto_detected_start_time: float
    auto_detected_end_time: float
    human_adjusted_start_time: float
    human_adjusted_end_time: float
    timing_adjustment_delta: float
    adjustment_reason: str
    creative_id: str = ""
    clip_id: str = ""
