"""Repositorio SQLite: feedback editorial (Fase 5.3)."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from aicos.application.editorial_metadata.ports import EditorialFeedbackWritePort
from aicos.database.db import EditorialFeedbackRow
from aicos.domain.editorial_metadata.entities import EditorialFeedbackSignal

logger = logging.getLogger(__name__)


class SqlEditorialFeedbackRepository(EditorialFeedbackWritePort):
    """Inserta filas en ``editorial_feedback``."""

    def append(self, session: Any, signal: EditorialFeedbackSignal, *, feedback_id: str) -> None:
        sess: Session = session
        row = EditorialFeedbackRow(
            id=feedback_id,
            clip_id=signal.clip_id,
            usefulness_score=float(signal.usefulness_score),
            continuity_score=float(signal.continuity_score),
            diversity_score=float(signal.diversity_score),
            narrative_quality=float(signal.narrative_quality),
            visual_quality=float(signal.visual_quality),
            human_feedback=signal.human_feedback or "",
        )
        sess.add(row)
        logger.debug("[EditorialFeedback] inserted id=%s clip=%s", feedback_id, signal.clip_id)
