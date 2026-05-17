"""Gestión de estados de revisión por escena."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from aicos.application.editorial_review.ports import EditorialSceneReviewPersistencePort
from aicos.domain.editorial_review.entities import EditorialSceneReviewState
from aicos.domain.editorial_review.enums import EditorialSceneReviewStatus
from aicos.domain.editorial_review.rules import validate_transition
from aicos.domain.editorial_review.scene_merge import scene_id_from_index

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class EditorialReviewSummary:
    session_id: str
    total_scenes: int
    pending: int
    accepted: int
    rejected: int
    merged: int
    edited: int


class TimelineReviewService:
    def __init__(self, *, persistence: EditorialSceneReviewPersistencePort) -> None:
        self._persistence = persistence

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def get_state(self, session: Any, session_id: str, scene_id: str) -> EditorialSceneReviewState:
        row = self._persistence.get(session, session_id, scene_id)
        if row is None:
            return EditorialSceneReviewState(
                scene_id=scene_id,
                status=EditorialSceneReviewStatus.PENDING,
                reviewed_at=None,
                reviewer="",
                correction_reason="",
                merged_into_scene_id=None,
                confidence_override=None,
                notes="",
            )
        return row

    def set_scene_status(
        self,
        session: Any,
        session_id: str,
        scene_id: str,
        *,
        status: str,
        reviewer: str = "human",
        correction_reason: str = "",
        notes: str = "",
        confidence_override: float | None = None,
        merged_into_scene_id: str | None = None,
    ) -> EditorialSceneReviewState:
        current = self.get_state(session, session_id, scene_id)
        ok, err = validate_transition(current.status, status)
        if not ok:
            raise ValueError(err)
        out = EditorialSceneReviewState(
            scene_id=scene_id,
            status=status,
            reviewed_at=self._now(),
            reviewer=(reviewer or "human")[:128],
            correction_reason=(correction_reason or "")[:512],
            merged_into_scene_id=merged_into_scene_id,
            confidence_override=confidence_override,
            notes=(notes or "")[:4000],
        )
        self._persistence.upsert(session, session_id, out)
        logger.info("[EditorialReview] scene=%s status=%s session=%s", scene_id, status, session_id)
        return out

    def batch_set_status(
        self,
        session: Any,
        session_id: str,
        scene_ids: tuple[str, ...],
        *,
        status: str,
        reviewer: str = "human",
        correction_reason: str = "",
    ) -> tuple[EditorialSceneReviewState, ...]:
        out: list[EditorialSceneReviewState] = []
        for sid in scene_ids:
            out.append(
                self.set_scene_status(
                    session,
                    session_id,
                    sid,
                    status=status,
                    reviewer=reviewer,
                    correction_reason=correction_reason,
                )
            )
        return tuple(out)

    def mark_edited(self, session: Any, session_id: str, scene_id: str, *, notes: str = "") -> EditorialSceneReviewState:
        return self.set_scene_status(
            session,
            session_id,
            scene_id,
            status=EditorialSceneReviewStatus.EDITED,
            correction_reason="manual_edit",
            notes=notes,
        )

    def get_review_summary(
        self,
        session: Any,
        session_id: str,
        *,
        scene_ids: tuple[str, ...],
    ) -> EditorialReviewSummary:
        known = {r.scene_id: r for r in self._persistence.list_by_session(session, session_id)}
        counts = {k: 0 for k in EditorialSceneReviewStatus.ALL}
        for sid in scene_ids:
            st = known.get(sid)
            status = st.status if st else EditorialSceneReviewStatus.PENDING
            counts[status] = counts.get(status, 0) + 1
        return EditorialReviewSummary(
            session_id=session_id,
            total_scenes=len(scene_ids),
            pending=counts.get(EditorialSceneReviewStatus.PENDING, 0),
            accepted=counts.get(EditorialSceneReviewStatus.ACCEPTED, 0),
            rejected=counts.get(EditorialSceneReviewStatus.REJECTED, 0),
            merged=counts.get(EditorialSceneReviewStatus.MERGED, 0),
            edited=counts.get(EditorialSceneReviewStatus.EDITED, 0),
        )

    def states_for_scene_indices(
        self,
        session: Any,
        session_id: str,
        indices: tuple[int, ...],
    ) -> dict[str, EditorialSceneReviewState]:
        return {
            scene_id_from_index(i): self.get_state(session, session_id, scene_id_from_index(i)) for i in indices
        }
