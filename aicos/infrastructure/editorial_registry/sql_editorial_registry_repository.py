"""Lectura SQLite del registry de sesiones editoriales."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from aicos.application.editorial_registry.ports import EditorialRegistryReadPort
from aicos.database.db import (
    CreativeTimelineRow,
    EditorialHumanFeedbackEventRow,
    EditorialSceneReviewRow,
    EditorialTrainingSessionRow,
    TimelineSceneRow,
)
from aicos.domain.editorial_registry.entities import EditorialRegistrySession
from aicos.domain.editorial_training.entities import EditorialTrainingSessionStatus

logger = logging.getLogger(__name__)


def _aware_utc(dt: datetime | None) -> datetime:
    if dt is None:
        return datetime.now(timezone.utc)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _meta_field(meta: dict | None, key: str) -> str:
    if not isinstance(meta, dict):
        return ""
    return str(meta.get(key) or "").strip()


class SqlEditorialRegistryRepository(EditorialRegistryReadPort):
    def list_sessions(
        self,
        session: Session,
        *,
        status: str | None = None,
    ) -> tuple[EditorialRegistrySession, ...]:
        q = select(EditorialTrainingSessionRow).order_by(EditorialTrainingSessionRow.updated_at.desc())
        if status:
            q = q.where(EditorialTrainingSessionRow.status == status)
        rows = session.scalars(q).all()
        if not rows:
            return ()

        session_ids = [r.id for r in rows]
        creative_ids = list({r.creative_id for r in rows if r.creative_id})

        timeline_by_creative: dict[str, CreativeTimelineRow] = {}
        if creative_ids:
            trows = session.scalars(
                select(CreativeTimelineRow).where(CreativeTimelineRow.creative_id.in_(creative_ids))
            ).all()
            timeline_by_creative = {t.creative_id: t for t in trows}

        scene_stats: dict[str, tuple[int, float]] = {}
        if timeline_by_creative:
            tl_ids = [t.id for t in timeline_by_creative.values()]
            agg = session.execute(
                select(
                    TimelineSceneRow.creative_timeline_id,
                    func.count(TimelineSceneRow.id),
                    func.max(TimelineSceneRow.end_time_sec),
                )
                .where(TimelineSceneRow.creative_timeline_id.in_(tl_ids))
                .group_by(TimelineSceneRow.creative_timeline_id)
            ).all()
            id_to_creative = {t.id: t.creative_id for t in timeline_by_creative.values()}
            for tl_id, cnt, max_end in agg:
                cid = id_to_creative.get(tl_id)
                if cid:
                    scene_stats[cid] = (int(cnt or 0), float(max_end or 0.0))

        review_sessions = set(
            session.scalars(
                select(EditorialSceneReviewRow.session_id).where(EditorialSceneReviewRow.session_id.in_(session_ids))
            ).all()
        )

        feedback_creatives: set[str] = set()
        if creative_ids:
            feedback_creatives = set(
                session.scalars(
                    select(EditorialHumanFeedbackEventRow.creative_id).where(
                        EditorialHumanFeedbackEventRow.creative_id.in_(creative_ids)
                    )
                ).all()
            )

        out: list[EditorialRegistrySession] = []
        for row in rows:
            meta = row.meta_json if isinstance(row.meta_json, dict) else {}
            corrections = row.corrections_json if isinstance(row.corrections_json, list) else []
            created = _aware_utc(row.created_at)
            updated = _aware_utc(row.updated_at)
            st = row.status or EditorialTrainingSessionStatus.DRAFT
            committed_at = updated if st == EditorialTrainingSessionStatus.COMMITTED else None
            cid = row.creative_id or ""
            sc, dur = scene_stats.get(cid, (0, 0.0))
            has_tl = cid in timeline_by_creative and sc > 0
            has_fb = (
                len(corrections) > 0
                or row.id in review_sessions
                or cid in feedback_creatives
            )
            out.append(
                EditorialRegistrySession(
                    session_id=row.id,
                    creative_id=cid,
                    creative_label=_meta_field(meta, "creative_label"),
                    project_label=_meta_field(meta, "project_label"),
                    product_category=_meta_field(meta, "product_category"),
                    status=st,
                    committed_at=committed_at,
                    created_at=created,
                    updated_at=updated,
                    scene_count=sc,
                    duration_seconds=round(dur, 3),
                    has_feedback=has_fb,
                    has_timeline=has_tl,
                    notes=_meta_field(meta, "notes"),
                    corrections_count=len(corrections),
                )
            )
        return tuple(out)
