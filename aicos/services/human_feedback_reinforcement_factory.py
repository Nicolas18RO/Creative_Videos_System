"""Factoría Fase 6.6 — refuerzo por feedback humano."""

from __future__ import annotations

from aicos.application.human_feedback.human_feedback_reinforcement_service import HumanFeedbackReinforcementService
from aicos.config import AppConfig, get_config
from aicos.infrastructure.human_feedback.sql_human_feedback_event_repository import SqlHumanFeedbackEventRepository


def build_human_feedback_reinforcement_service(app_cfg: AppConfig | None = None) -> HumanFeedbackReinforcementService:
    cfg = app_cfg or get_config()
    return HumanFeedbackReinforcementService(cfg.human_feedback_reinforcement, SqlHumanFeedbackEventRepository())
