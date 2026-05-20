"""Persistencia SQLite de overrides de categoría editorial."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from aicos.application.editorial_category.ports import EditorialCategoryOverridePersistencePort
from aicos.database.db import EditorialSceneCategoryOverrideRow
from aicos.domain.editorial_category.entities import EditorialSceneCategoryOverride


def _aware(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _to_entity(row: EditorialSceneCategoryOverrideRow) -> EditorialSceneCategoryOverride:
    return EditorialSceneCategoryOverride(
        session_id=row.session_id,
        scene_index=int(row.scene_index),
        auto_narrative_role=row.auto_narrative_role or "NATURAL",
        human_narrative_role=row.human_narrative_role,
        updated_at=_aware(row.updated_at),
        reviewer=row.reviewer or "human",
    )


class SqlEditorialCategoryOverrideRepository(EditorialCategoryOverridePersistencePort):
    def get(self, session: Session, session_id: str, scene_index: int) -> EditorialSceneCategoryOverride | None:
        row = session.scalar(
            select(EditorialSceneCategoryOverrideRow).where(
                EditorialSceneCategoryOverrideRow.session_id == session_id,
                EditorialSceneCategoryOverrideRow.scene_index == scene_index,
            )
        )
        return _to_entity(row) if row else None

    def list_by_session(self, session: Session, session_id: str) -> tuple[EditorialSceneCategoryOverride, ...]:
        rows = session.scalars(
            select(EditorialSceneCategoryOverrideRow)
            .where(EditorialSceneCategoryOverrideRow.session_id == session_id)
            .order_by(EditorialSceneCategoryOverrideRow.scene_index)
        ).all()
        return tuple(_to_entity(r) for r in rows)

    def upsert(self, session: Session, override: EditorialSceneCategoryOverride) -> None:
        row = session.scalar(
            select(EditorialSceneCategoryOverrideRow).where(
                EditorialSceneCategoryOverrideRow.session_id == override.session_id,
                EditorialSceneCategoryOverrideRow.scene_index == override.scene_index,
            )
        )
        if row is None:
            row = EditorialSceneCategoryOverrideRow(
                id=str(uuid.uuid4()),
                session_id=override.session_id,
                scene_index=override.scene_index,
                auto_narrative_role=override.auto_narrative_role,
                human_narrative_role=override.human_narrative_role,
                reviewer=override.reviewer,
            )
            session.add(row)
        else:
            row.auto_narrative_role = override.auto_narrative_role
            row.human_narrative_role = override.human_narrative_role
            row.reviewer = override.reviewer
        session.flush()
