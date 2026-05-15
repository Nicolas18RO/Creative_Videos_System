"""Dominio Fase 6.6 — refuerzo por feedback humano (memoria editorial acumulativa)."""

from aicos.domain.human_feedback.entities import EditorialHumanFeedbackEvent
from aicos.domain.human_feedback.rules import (
    HumanFeedbackAccumulationParams,
    accumulate_clip_boosts,
    time_decay_multiplier,
)

__all__ = [
    "EditorialHumanFeedbackEvent",
    "HumanFeedbackAccumulationParams",
    "accumulate_clip_boosts",
    "time_decay_multiplier",
]
