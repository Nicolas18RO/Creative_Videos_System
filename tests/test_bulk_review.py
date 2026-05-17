"""Tests BulkReviewService."""

from __future__ import annotations

from unittest.mock import MagicMock

from aicos.application.editorial_review.bulk_review_service import BulkReviewService
from aicos.application.editorial_review.timeline_review_service import TimelineReviewService
from aicos.domain.editorial_review.enums import EditorialSceneReviewStatus
from tests.test_editorial_review_service import _MemReview


def test_accept_all_pending() -> None:
    repo = _MemReview()
    review = TimelineReviewService(persistence=repo)
    bulk = BulkReviewService(review=review)
    summary = bulk.accept_all_pending(MagicMock(), "s1", (0, 1, 2))
    assert summary.pending == 0
    assert summary.accepted == 3
    st = review.get_state(MagicMock(), "s1", "1")
    assert st.status == EditorialSceneReviewStatus.ACCEPTED


def test_auto_accept_high_confidence() -> None:
    repo = _MemReview()
    review = TimelineReviewService(persistence=repo)
    bulk = BulkReviewService(review=review)
    conf = {"0": 0.9, "1": 0.2, "2": 0.8}
    summary = bulk.auto_accept_high_confidence(MagicMock(), "s1", (0, 1, 2), confidence_by_scene=conf, threshold=0.75)
    assert summary.accepted == 2
    assert summary.pending == 1
