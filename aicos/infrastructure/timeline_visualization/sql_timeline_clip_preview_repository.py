"""Persistencia SQLite de previews del timeline visual."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from aicos.application.timeline_visualization.ports import TimelineClipPreviewPersistencePort
from aicos.database.db import TimelineClipPreviewRow
from aicos.domain.timeline_visualization.entities import TimelineClipPreview

logger = logging.getLogger(__name__)


def _row_to_domain(row: TimelineClipPreviewRow) -> TimelineClipPreview:
    return TimelineClipPreview(
        clip_id=row.clip_id or "",
        scene_index=int(row.scene_index),
        thumbnail_path=row.thumbnail_path or "",
        preview_video_path=row.preview_video_path or "",
        start_time=float(row.start_time),
        end_time=float(row.end_time),
        duration=float(row.duration),
        motion_score=float(row.motion_score),
        narrative_role=row.narrative_role or "",
        visual_cluster_id=row.visual_cluster_id or "",
        timeline_position=float(row.timeline_position),
    )


class SqlTimelineClipPreviewRepository(TimelineClipPreviewPersistencePort):
    def list_by_creative_id(self, session: Any, creative_id: str) -> tuple[TimelineClipPreview, ...]:
        db: Session = session
        rows = db.scalars(
            select(TimelineClipPreviewRow)
            .where(TimelineClipPreviewRow.creative_id == creative_id)
            .order_by(TimelineClipPreviewRow.scene_index)
        ).all()
        return tuple(_row_to_domain(r) for r in rows)

    def upsert_batch(self, session: Any, creative_id: str, previews: tuple[TimelineClipPreview, ...]) -> None:
        db: Session = session
        db.execute(delete(TimelineClipPreviewRow).where(TimelineClipPreviewRow.creative_id == creative_id))
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        for p in previews:
            db.add(
                TimelineClipPreviewRow(
                    id=str(uuid.uuid4()),
                    creative_id=creative_id,
                    scene_index=p.scene_index,
                    clip_id=p.clip_id,
                    thumbnail_path=p.thumbnail_path,
                    preview_video_path=p.preview_video_path,
                    start_time=p.start_time,
                    end_time=p.end_time,
                    duration=p.duration,
                    motion_score=p.motion_score,
                    narrative_role=p.narrative_role,
                    visual_cluster_id=p.visual_cluster_id,
                    timeline_position=p.timeline_position,
                    created_at=now,
                )
            )
        db.flush()
        logger.debug("[TimelineViz] upserted %s previews for creative=%s", len(previews), creative_id)

    def delete_by_creative_id(self, session: Any, creative_id: str) -> None:
        db: Session = session
        db.execute(delete(TimelineClipPreviewRow).where(TimelineClipPreviewRow.creative_id == creative_id))
        db.flush()
