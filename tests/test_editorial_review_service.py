"""Tests TimelineReviewService (Fase 6.7.1)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from aicos.application.editorial_review.timeline_review_service import TimelineReviewService
from aicos.domain.editorial_review.enums import EditorialSceneReviewStatus


class _MemReview:
    def __init__(self) -> None:
        self.data: dict[tuple[str, str], object] = {}

    def list_by_session(self, session, session_id: str):
        return tuple(v for (sid, _), v in self.data.items() if sid == session_id)

    def get(self, session, session_id: str, scene_id: str):
        return self.data.get((session_id, scene_id))

    def upsert(self, session, session_id: str, state) -> None:
        self.data[(session_id, state.scene_id)] = state

    def upsert_many(self, session, session_id: str, states) -> None:
        for st in states:
            self.upsert(session, session_id, st)

    def delete_by_session(self, session, session_id: str) -> None:
        keys = [k for k in self.data if k[0] == session_id]
        for k in keys:
            del self.data[k]


def test_set_and_batch_status() -> None:
    svc = TimelineReviewService(persistence=_MemReview())
    st = svc.set_scene_status(MagicMock(), "sess1", "0", status=EditorialSceneReviewStatus.ACCEPTED)
    assert st.status == EditorialSceneReviewStatus.ACCEPTED
    summary = svc.get_review_summary(MagicMock(), "sess1", scene_ids=("0", "1"))
    assert summary.total_scenes == 2
    assert summary.pending == 1


def test_cannot_accept_to_pending() -> None:
    svc = TimelineReviewService(persistence=_MemReview())
    svc.set_scene_status(MagicMock(), "s", "1", status=EditorialSceneReviewStatus.ACCEPTED)
    with pytest.raises(ValueError, match="accepted_scene_cannot_be_pending"):
        svc.set_scene_status(MagicMock(), "s", "1", status=EditorialSceneReviewStatus.PENDING)
