"""Puertos de persistencia y lectura de eventos de feedback editorial (Fase 6.6)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol

from aicos.domain.human_feedback.entities import EditorialHumanFeedbackEvent


class HumanFeedbackEventPersistencePort(Protocol):
    def append(self, session: Any, event: EditorialHumanFeedbackEvent) -> None:
        ...

    def list_since(self, session: Any, *, since: datetime) -> tuple[EditorialHumanFeedbackEvent, ...]:
        ...
