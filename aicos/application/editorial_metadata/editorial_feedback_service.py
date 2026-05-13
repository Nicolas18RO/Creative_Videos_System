"""Servicio de aplicación: feedback editorial humano."""

from __future__ import annotations

import logging
import uuid
from typing import Any

from aicos.application.editorial_metadata.ports import EditorialFeedbackWritePort
from aicos.config import EditorialMetadataConfig
from aicos.domain.editorial_metadata.entities import EditorialFeedbackSignal

logger = logging.getLogger(__name__)


class EditorialFeedbackService:
    """Persistencia opcional de señales editoriales."""

    def __init__(self, *, write_port: EditorialFeedbackWritePort, cfg: EditorialMetadataConfig) -> None:
        self._write = write_port
        self._cfg = cfg

    def submit(self, session: Any, signal: EditorialFeedbackSignal) -> str:
        if not self._cfg.persist_feedback:
            logger.info(
                "[EditorialFeedback] clip=%s usefulness=%.2f persisted=False",
                signal.clip_id,
                signal.usefulness_score,
            )
            return ""
        fid = str(uuid.uuid4())
        self._write.append(session, signal, feedback_id=fid)
        logger.info(
            "[EditorialFeedback] clip=%s usefulness=%.2f narrative_q=%.2f visual_q=%.2f",
            signal.clip_id,
            signal.usefulness_score,
            signal.narrative_quality,
            signal.visual_quality,
        )
        return fid
