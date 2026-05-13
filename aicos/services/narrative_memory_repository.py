"""Persistencia SQLite para Narrative Memory (Fase 3)."""

from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from aicos.database.db import (
    NarrativeClipSelectionHistoryRow,
    NarrativeContinuityDecisionRow,
    NarrativeMemorySnapshotRow,
    NarrativeSessionRow,
)

logger = logging.getLogger(__name__)


def ensure_narrative_session(session: Session, correlation_id: str, *, project_id: str | None = None) -> None:
    """Garantiza fila en ``narrative_sessions`` (id = correlation_id)."""
    row = session.get(NarrativeSessionRow, correlation_id)
    if row is None:
        session.add(NarrativeSessionRow(id=correlation_id, project_id=project_id))
        session.flush()
        logger.info("[NarrativeMemory] session_created id=%s", correlation_id)


def load_snapshot_by_scene_index(
    session: Session, correlation_id: str, scene_index: int
) -> dict[str, Any] | None:
    """Carga instantánea exacta para ``scene_index`` (p. ej. estado tras cerrar esa escena)."""
    stmt = (
        select(NarrativeMemorySnapshotRow)
        .where(
            NarrativeMemorySnapshotRow.narrative_session_id == correlation_id,
            NarrativeMemorySnapshotRow.scene_index == scene_index,
        )
        .limit(1)
    )
    snap = session.scalars(stmt).first()
    if snap is None:
        return None
    return dict(snap.state_payload)


def load_latest_state_payload(
    session: Session, correlation_id: str, *, max_scene_index: int | None = None
) -> dict[str, Any] | None:
    """Carga el último ``state_payload`` conocido (opcionalmente hasta ``max_scene_index`` inclusive)."""
    stmt = select(NarrativeMemorySnapshotRow).where(
        NarrativeMemorySnapshotRow.narrative_session_id == correlation_id
    )
    if max_scene_index is not None:
        stmt = stmt.where(NarrativeMemorySnapshotRow.scene_index <= max_scene_index)
    stmt = stmt.order_by(NarrativeMemorySnapshotRow.scene_index.desc()).limit(1)
    snap = session.scalars(stmt).first()
    if snap is None:
        return None
    return dict(snap.state_payload)


def save_state_snapshot(
    session: Session,
    correlation_id: str,
    scene_index: int,
    state_payload: dict[str, Any],
) -> None:
    """Inserta instantánea de estado tras una escena."""
    ensure_narrative_session(session, correlation_id)
    session.add(
        NarrativeMemorySnapshotRow(
            id=str(uuid.uuid4()),
            narrative_session_id=correlation_id,
            scene_index=scene_index,
            state_payload=state_payload,
        )
    )
    session.flush()
    logger.info("[NarrativeMemory] snapshot_saved session=%s scene_index=%s", correlation_id, scene_index)


def log_clip_selection(
    session: Session,
    correlation_id: str,
    scene_index: int,
    *,
    clip_id: str,
    rank_chosen: int,
    final_score: float,
    continuity_blend: float | None,
    extra: dict[str, Any] | None = None,
) -> None:
    """Historial de clip priorizado."""
    ensure_narrative_session(session, correlation_id)
    session.add(
        NarrativeClipSelectionHistoryRow(
            id=str(uuid.uuid4()),
            narrative_session_id=correlation_id,
            scene_index=scene_index,
            clip_id=clip_id,
            rank_chosen=rank_chosen,
            final_score=final_score,
            continuity_blend=continuity_blend,
            extra_json=extra,
        )
    )
    session.flush()


def log_continuity_decision(
    session: Session,
    correlation_id: str,
    scene_index: int,
    *,
    clip_id: str,
    decision_type: str,
    reason_code: str,
    factors: dict[str, Any] | None = None,
) -> None:
    """Auditoría de decisión de continuidad."""
    ensure_narrative_session(session, correlation_id)
    session.add(
        NarrativeContinuityDecisionRow(
            id=str(uuid.uuid4()),
            narrative_session_id=correlation_id,
            scene_index=scene_index,
            clip_id=clip_id,
            decision_type=decision_type,
            reason_code=reason_code,
            factors_json=factors,
        )
    )
    session.flush()
