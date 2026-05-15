"""Dominio Fase 6.7 — espacio de entrenamiento editorial (sesiones y correcciones)."""

from aicos.domain.editorial_training.entities import (
    EditorialTrainingCorrectionItem,
    EditorialTrainingSession,
    EditorialTrainingSessionStatus,
)
from aicos.domain.editorial_training.rules import validate_correction_reward

__all__ = [
    "EditorialTrainingCorrectionItem",
    "EditorialTrainingSession",
    "EditorialTrainingSessionStatus",
    "validate_correction_reward",
]
