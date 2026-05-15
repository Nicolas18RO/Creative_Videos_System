"""Digest de historial de uso de clips (Fase 4) para el motor 6.2."""

from __future__ import annotations

import logging
from typing import Any, Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from aicos.application.editorial_pattern_engine.ports import ClipUsageHistoryDigestPort
from aicos.database.db import ClipUsageHistoryRow
from aicos.domain.editorial_pattern_engine.entities import ClipUsagePressureDigest, PerClipUsagePressure

logger = logging.getLogger(__name__)


class SqlClipUsageHistoryDigestAdapter(ClipUsageHistoryDigestPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def build_digest(self, session: Any, clip_ids: Sequence[str]) -> ClipUsagePressureDigest:
        sess = session if session is not None else self._session
        ids = tuple(dict.fromkeys(str(x) for x in clip_ids if x))
        if not ids:
            return ClipUsagePressureDigest(
                by_clip=tuple(),
                timeline_source_entropy=0.0,
                max_cluster_streak_length=0,
            )
        stmt = (
            select(
                ClipUsageHistoryRow.clip_id,
                func.count().label("cnt"),
                func.count(func.distinct(ClipUsageHistoryRow.correlation_id)).label("sessions"),
                func.avg(ClipUsageHistoryRow.final_score).label("avg_sc"),
            )
            .where(ClipUsageHistoryRow.clip_id.in_(ids))
            .group_by(ClipUsageHistoryRow.clip_id)
        )
        rows: dict[str, tuple[int, int, float]] = {}
        for clip_id, cnt, sessions, avg_sc in sess.execute(stmt):
            rows[str(clip_id)] = (int(cnt or 0), int(sessions or 0), float(avg_sc or 0.0))
        pressures: list[PerClipUsagePressure] = []
        for cid in ids:
            hit = rows.get(cid)
            if hit is None:
                pressures.append(
                    PerClipUsagePressure(
                        clip_id=cid,
                        global_selection_count=0,
                        distinct_sessions=0,
                        mean_final_score=0.0,
                    )
                )
            else:
                cnt, sessions, avg_sc = hit
                pressures.append(
                    PerClipUsagePressure(
                        clip_id=cid,
                        global_selection_count=cnt,
                        distinct_sessions=sessions,
                        mean_final_score=avg_sc,
                    )
                )
        logger.debug("[PatternEngineUsage] digest clips=%s hits=%s", len(ids), len(rows))
        return ClipUsagePressureDigest(
            by_clip=tuple(pressures),
            timeline_source_entropy=0.0,
            max_cluster_streak_length=0,
        )
