"""Persistencia SQLite de eventos de feedback editorial humano (Fase 6.6)."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from aicos.application.human_feedback.ports import HumanFeedbackEventPersistencePort
from aicos.database.db import EditorialHumanFeedbackEventRow
from aicos.domain.human_feedback.entities import EditorialHumanFeedbackEvent

logger = logging.getLogger(__name__)


def _utc_naive(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


def _aware_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _row_to_domain(row: EditorialHumanFeedbackEventRow) -> EditorialHumanFeedbackEvent:
    raw = row.created_at
    if raw is None:
        created = datetime.now(timezone.utc)
    else:
        created = _aware_utc(raw)
    return EditorialHumanFeedbackEvent(
        id=row.id,
        created_at=created,
        event_kind=row.event_kind or "generic",
        reward=float(row.reward or 0.0),
        creative_id=row.creative_id,
        clip_id=row.clip_id,
        replaced_clip_id=row.replaced_clip_id,
        scene_index=row.scene_index,
        narrative_function=row.narrative_function,
        transition_type=row.transition_type,
        query_fingerprint=row.query_fingerprint,
    )


class SqlHumanFeedbackEventRepository(HumanFeedbackEventPersistencePort):
    def append(self, session: Session, event: EditorialHumanFeedbackEvent) -> None:
        row = EditorialHumanFeedbackEventRow(
            id=event.id,
            created_at=_utc_naive(event.created_at),
            event_kind=event.event_kind,
            reward=float(event.reward),
            creative_id=event.creative_id,
            clip_id=event.clip_id,
            replaced_clip_id=event.replaced_clip_id,
            scene_index=event.scene_index,
            narrative_function=event.narrative_function,
            transition_type=event.transition_type,
            query_fingerprint=event.query_fingerprint,
            payload_json=None,
        )
        session.add(row)
        session.flush()
        logger.debug("[HumanFeedbackReinforcement] persisted id=%s", event.id)

    def list_since(self, session: Session, *, since: datetime) -> tuple[EditorialHumanFeedbackEvent, ...]:
        since_naive = _utc_naive(since)
        rows = list(
            session.scalars(
                select(EditorialHumanFeedbackEventRow)
                .where(EditorialHumanFeedbackEventRow.created_at >= since_naive)
                .order_by(EditorialHumanFeedbackEventRow.created_at.desc())
                .limit(8000)
            ).all()
        )
        return tuple(_row_to_domain(r) for r in reversed(rows))
