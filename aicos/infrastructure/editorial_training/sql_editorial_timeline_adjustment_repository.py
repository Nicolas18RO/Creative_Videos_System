"""Persistencia SQLite de ajustes de timing editorial (Fase 6.8)."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select

from aicos.application.editorial_training.ports import EditorialTimelineAdjustmentPersistencePort
from aicos.database.db import EditorialTimelineAdjustmentRow
from aicos.domain.editorial_training.entities import EditorialTimelineAdjustment


def _to_entity(row: EditorialTimelineAdjustmentRow) -> EditorialTimelineAdjustment:
    return EditorialTimelineAdjustment(
        session_id=row.session_id,
        scene_index=int(row.scene_index),
        auto_detected_start_time=float(row.auto_detected_start_time),
        auto_detected_end_time=float(row.auto_detected_end_time),
        human_adjusted_start_time=float(row.human_adjusted_start_time),
        human_adjusted_end_time=float(row.human_adjusted_end_time),
        timing_adjustment_delta=float(row.timing_adjustment_delta),
        adjustment_reason=row.adjustment_reason or "",
        creative_id=row.creative_id or "",
        clip_id=row.clip_id or "",
    )


class SqlEditorialTimelineAdjustmentRepository(EditorialTimelineAdjustmentPersistencePort):
    def list_by_session(self, session: Any, session_id: str) -> tuple[EditorialTimelineAdjustment, ...]:
        rows = session.scalars(
            select(EditorialTimelineAdjustmentRow)
            .where(EditorialTimelineAdjustmentRow.session_id == session_id)
            .order_by(EditorialTimelineAdjustmentRow.scene_index)
        ).all()
        return tuple(_to_entity(r) for r in rows)

    def upsert(self, session: Any, adjustment: EditorialTimelineAdjustment) -> None:
        row = session.scalar(
            select(EditorialTimelineAdjustmentRow).where(
                EditorialTimelineAdjustmentRow.session_id == adjustment.session_id,
                EditorialTimelineAdjustmentRow.scene_index == adjustment.scene_index,
            )
        )
        if row is None:
            row = EditorialTimelineAdjustmentRow(
                id=str(uuid.uuid4()),
                session_id=adjustment.session_id,
                creative_id=adjustment.creative_id,
                scene_index=adjustment.scene_index,
                clip_id=adjustment.clip_id,
                auto_detected_start_time=adjustment.auto_detected_start_time,
                auto_detected_end_time=adjustment.auto_detected_end_time,
                human_adjusted_start_time=adjustment.human_adjusted_start_time,
                human_adjusted_end_time=adjustment.human_adjusted_end_time,
                timing_adjustment_delta=adjustment.timing_adjustment_delta,
                adjustment_reason=adjustment.adjustment_reason,
            )
            session.add(row)
        else:
            row.human_adjusted_start_time = adjustment.human_adjusted_start_time
            row.human_adjusted_end_time = adjustment.human_adjusted_end_time
            row.timing_adjustment_delta = adjustment.timing_adjustment_delta
            row.adjustment_reason = adjustment.adjustment_reason
            row.clip_id = adjustment.clip_id
        session.flush()
