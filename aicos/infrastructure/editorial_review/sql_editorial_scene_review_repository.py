"""SQLite — estados de revisión editorial por escena."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from aicos.application.editorial_review.ports import (
    EditorialSceneMergePersistencePort,
    EditorialSceneReviewPersistencePort,
)
from aicos.database.db import EditorialSceneMergeRow, EditorialSceneReviewRow
from aicos.domain.editorial_review.entities import EditorialSceneMergeRecord, EditorialSceneReviewState

logger = logging.getLogger(__name__)


def _aware(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _row_to_review(row: EditorialSceneReviewRow) -> EditorialSceneReviewState:
    return EditorialSceneReviewState(
        scene_id=row.scene_id,
        status=row.status or "pending",
        reviewed_at=_aware(row.updated_at),
        reviewer=row.reviewer or "",
        correction_reason=row.correction_reason or "",
        merged_into_scene_id=row.merged_into_scene_id,
        confidence_override=row.confidence_override,
        notes=row.notes or "",
    )


class SqlEditorialSceneReviewRepository(EditorialSceneReviewPersistencePort):
    def list_by_session(self, session: Any, session_id: str) -> tuple[EditorialSceneReviewState, ...]:
        db: Session = session
        rows = db.scalars(
            select(EditorialSceneReviewRow).where(EditorialSceneReviewRow.session_id == session_id)
        ).all()
        return tuple(_row_to_review(r) for r in rows)

    def get(self, session: Any, session_id: str, scene_id: str) -> EditorialSceneReviewState | None:
        db: Session = session
        row = db.scalars(
            select(EditorialSceneReviewRow).where(
                EditorialSceneReviewRow.session_id == session_id,
                EditorialSceneReviewRow.scene_id == scene_id,
            )
        ).first()
        return _row_to_review(row) if row else None

    def upsert(self, session: Any, session_id: str, state: EditorialSceneReviewState) -> None:
        db: Session = session
        row = db.scalars(
            select(EditorialSceneReviewRow).where(
                EditorialSceneReviewRow.session_id == session_id,
                EditorialSceneReviewRow.scene_id == state.scene_id,
            )
        ).first()
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if row is None:
            row = EditorialSceneReviewRow(
                id=str(uuid.uuid4()),
                session_id=session_id,
                scene_id=state.scene_id,
                status=state.status,
                reviewer=state.reviewer,
                correction_reason=state.correction_reason,
                merged_into_scene_id=state.merged_into_scene_id,
                confidence_override=state.confidence_override,
                notes=state.notes,
                created_at=now,
                updated_at=now,
            )
            db.add(row)
        else:
            row.status = state.status
            row.reviewer = state.reviewer
            row.correction_reason = state.correction_reason
            row.merged_into_scene_id = state.merged_into_scene_id
            row.confidence_override = state.confidence_override
            row.notes = state.notes
            row.updated_at = now
        db.flush()

    def upsert_many(self, session: Any, session_id: str, states: tuple[EditorialSceneReviewState, ...]) -> None:
        for st in states:
            self.upsert(session, session_id, st)

    def delete_by_session(self, session: Any, session_id: str) -> None:
        db: Session = session
        db.execute(delete(EditorialSceneReviewRow).where(EditorialSceneReviewRow.session_id == session_id))
        db.flush()


class SqlEditorialSceneMergeRepository(EditorialSceneMergePersistencePort):
    def list_by_session(self, session: Any, session_id: str) -> tuple[EditorialSceneMergeRecord, ...]:
        db: Session = session
        rows = db.scalars(
            select(EditorialSceneMergeRow).where(EditorialSceneMergeRow.session_id == session_id)
        ).all()
        return tuple(
            EditorialSceneMergeRecord(
                source_scene_a=r.source_scene_a,
                source_scene_b=r.source_scene_b,
                resulting_scene_id=r.resulting_scene_id,
                session_id=r.session_id,
                created_at=_aware(r.created_at) or datetime.now(timezone.utc),
            )
            for r in rows
        )

    def save(self, session: Any, record: EditorialSceneMergeRecord) -> None:
        db: Session = session
        db.add(
            EditorialSceneMergeRow(
                id=str(uuid.uuid4()),
                session_id=record.session_id,
                source_scene_a=record.source_scene_a,
                source_scene_b=record.source_scene_b,
                resulting_scene_id=record.resulting_scene_id,
                created_at=record.created_at.replace(tzinfo=None)
                if record.created_at.tzinfo
                else record.created_at,
            )
        )
        db.flush()
        logger.debug("[EditorialReview] merge saved session=%s", record.session_id)
