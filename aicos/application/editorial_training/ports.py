"""Puertos de persistencia de sesiones de entrenamiento editorial (Fase 6.7)."""

from __future__ import annotations

from typing import Any, Protocol

from aicos.domain.editorial_dataset.entities import CreativeTimeline
from aicos.domain.editorial_training.entities import EditorialTrainingSession


class EditorialStyleEmbeddingAttachPort(Protocol):
    """Puente hacia Fase 6.3 (persistencia + índice) sin acoplar la aplicación a factorías concretas."""

    def attach_if_configured(self, session: Any, timeline: CreativeTimeline) -> CreativeTimeline:
        ...


class EditorialTrainingSessionPersistencePort(Protocol):
    def get_by_id(self, session: Any, session_id: str) -> EditorialTrainingSession | None:
        ...

    def save(self, session: Any, training: EditorialTrainingSession) -> None:
        ...
