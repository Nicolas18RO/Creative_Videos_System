"""Factoría Fase 6.8 — edición precisa de timeline."""

from __future__ import annotations

from aicos.application.editorial_training.timeline_precision_service import TimelinePrecisionService
from aicos.config import AppConfig
from aicos.infrastructure.editorial_dataset.sqlite_creative_timeline_repository import SqlCreativeTimelineRepository
from aicos.infrastructure.editorial_training.sql_editorial_timeline_adjustment_repository import (
    SqlEditorialTimelineAdjustmentRepository,
)
from aicos.services.editorial_training_factory import build_editorial_training_workspace_service


def build_timeline_precision_service(cfg: AppConfig | None = None) -> TimelinePrecisionService:
    _ = cfg
    timeline_read = SqlCreativeTimelineRepository()
    workspace = build_editorial_training_workspace_service()
    return TimelinePrecisionService(
        timeline_read=timeline_read,
        workspace=workspace,
        adjustments=SqlEditorialTimelineAdjustmentRepository(),
    )
