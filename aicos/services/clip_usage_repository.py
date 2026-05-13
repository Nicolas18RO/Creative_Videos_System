"""Persistencia de historial de uso de clips (Fase 4)."""

from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy.orm import Session

from aicos.database.db import ClipUsageHistoryRow

logger = logging.getLogger(__name__)


def append_clip_usage_history(
    session: Session,
    *,
    correlation_id: str,
    scene_index: int,
    clip_id: str,
    source_video_id: str,
    visual_cluster_id: str,
    final_score: float,
    penalties_json: dict[str, Any] | None = None,
) -> None:
    """Inserta un registro de selección final para analytics y depuración."""
    row = ClipUsageHistoryRow(
        id=str(uuid.uuid4()),
        correlation_id=correlation_id,
        scene_index=scene_index,
        clip_id=clip_id,
        source_video_id=(source_video_id or "")[:32],
        visual_cluster_id=(visual_cluster_id or "")[:32],
        final_score=float(final_score),
        penalties_json=penalties_json,
    )
    session.add(row)
    session.flush()
    logger.info(
        "[ClipUsageHistory] correlation_id=%s scene=%s clip=%s src=%s cluster=%s",
        correlation_id,
        scene_index,
        clip_id,
        (source_video_id or "")[:12],
        (visual_cluster_id or "")[:12],
    )
