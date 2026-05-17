"""Acciones masivas sobre estados de revisión."""

from __future__ import annotations

import logging
from typing import Any

from aicos.application.editorial_review.timeline_review_service import EditorialReviewSummary, TimelineReviewService
from aicos.domain.editorial_review.enums import EditorialSceneReviewStatus
from aicos.domain.editorial_review.scene_merge import scene_id_from_index

logger = logging.getLogger(__name__)


class BulkReviewService:
    def __init__(self, *, review: TimelineReviewService) -> None:
        self._review = review

    def accept_all_pending(
        self, session: Any, session_id: str, scene_indices: tuple[int, ...]
    ) -> EditorialReviewSummary:
        pending = self._pending_ids(session, session_id, scene_indices)
        self._review.batch_set_status(
            session, session_id, pending, status=EditorialSceneReviewStatus.ACCEPTED, correction_reason="bulk_accept"
        )
        return self._summary(session, session_id, scene_indices)

    def reject_all_pending(
        self, session: Any, session_id: str, scene_indices: tuple[int, ...]
    ) -> EditorialReviewSummary:
        pending = self._pending_ids(session, session_id, scene_indices)
        self._review.batch_set_status(
            session, session_id, pending, status=EditorialSceneReviewStatus.REJECTED, correction_reason="bulk_reject"
        )
        return self._summary(session, session_id, scene_indices)

    def auto_accept_high_confidence(
        self,
        session: Any,
        session_id: str,
        scene_indices: tuple[int, ...],
        *,
        confidence_by_scene: dict[str, float],
        threshold: float = 0.75,
    ) -> EditorialReviewSummary:
        pending = self._pending_ids(session, session_id, scene_indices)
        to_accept: list[str] = []
        for sid in pending:
            if confidence_by_scene.get(sid, 0.0) >= threshold:
                to_accept.append(sid)
        if to_accept:
            self._review.batch_set_status(
                session,
                session_id,
                tuple(to_accept),
                status=EditorialSceneReviewStatus.ACCEPTED,
                correction_reason="auto_accept_high_confidence",
            )
        return self._summary(session, session_id, scene_indices)

    def mark_remaining_pending(
        self, session: Any, session_id: str, scene_indices: tuple[int, ...]
    ) -> EditorialReviewSummary:
        ids = tuple(scene_id_from_index(i) for i in scene_indices)
        states = []
        for sid in ids:
            st = self._review.get_state(session, session_id, sid)
            if st.status == EditorialSceneReviewStatus.MERGED:
                continue
            states.append(
                self._review.set_scene_status(
                    session, session_id, sid, status=EditorialSceneReviewStatus.PENDING, correction_reason="reset_pending"
                )
            )
        return self._summary(session, session_id, scene_indices)

    def reset_review_states(self, session: Any, session_id: str, scene_indices: tuple[int, ...]) -> EditorialReviewSummary:
        return self.mark_remaining_pending(session, session_id, scene_indices)

    def _pending_ids(self, session: Any, session_id: str, scene_indices: tuple[int, ...]) -> tuple[str, ...]:
        out: list[str] = []
        for i in scene_indices:
            sid = scene_id_from_index(i)
            st = self._review.get_state(session, session_id, sid)
            if st.status == EditorialSceneReviewStatus.PENDING:
                out.append(sid)
        return tuple(out)

    def _summary(self, session: Any, session_id: str, scene_indices: tuple[int, ...]) -> EditorialReviewSummary:
        ids = tuple(scene_id_from_index(i) for i in scene_indices)
        return self._review.get_review_summary(session, session_id, scene_ids=ids)
