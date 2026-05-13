"""Feedback y recalibración (MVP: persistencia + hooks; pesos vía config en runtime)."""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass

from aicos.application.cinematic.ports import FeedbackEventRepositoryPort
from aicos.domain.cinematic.entities import FeedbackEvent

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class FeedbackLearningService:
    """Registra eventos; la recalibración fina de pesos queda para fases posteriores."""

    events: FeedbackEventRepositoryPort | None = None

    def record(
        self,
        *,
        event_type: str,
        clip_id: str | None = None,
        scene_id: str | None = None,
        project_id: str | None = None,
        rejection_reason: str | None = None,
        acceptance_score: float | None = None,
        payload: dict | None = None,
    ) -> str:
        t0 = time.perf_counter()
        eid = str(uuid.uuid4())
        ev = FeedbackEvent(
            id=eid,
            event_type=event_type,
            clip_id=clip_id,
            scene_id=scene_id,
            project_id=project_id,
            rejection_reason=rejection_reason,
            acceptance_score=acceptance_score,
            payload=payload,
        )
        if self.events is not None:
            self.events.append_event(ev)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        logger.info(
            "feedback_learning stage=persist event=%s clip=%s elapsed_ms=%.1f",
            event_type,
            clip_id,
            elapsed_ms,
        )
        return eid

    def recalibrate_weights(self) -> dict[str, float]:
        """Placeholder: devuelve pesos actuales sin mutar ``config.yaml``."""
        logger.info("feedback_learning stage=recalibrate note=no_op_mvp")
        return {}
