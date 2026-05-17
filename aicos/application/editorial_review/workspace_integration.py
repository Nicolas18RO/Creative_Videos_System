"""Integración revisión ↔ workspace de entrenamiento."""

from __future__ import annotations

from typing import Any

from aicos.application.editorial_review.presentation import summary_to_out
from aicos.application.editorial_review.timeline_review_service import TimelineReviewService
from aicos.application.editorial_dataset.ports import CreativeTimelinePersistenceReadPort
from aicos.domain.editorial_review.scene_merge import scene_id_from_index
from aicos.models.schemas import EditorialReviewSummaryOut


def load_review_summary_for_session(
    session: Any,
    session_id: str,
    creative_id: str,
    *,
    timeline_read: CreativeTimelinePersistenceReadPort,
    review_svc: TimelineReviewService,
    review_repo: Any,
) -> EditorialReviewSummaryOut | None:
    tl = timeline_read.get_by_creative_id(session, creative_id)
    if tl is None:
        return None
    indices = tuple(s.scene_index for s in tl.timeline_scenes)
    scene_ids = tuple(scene_id_from_index(i) for i in indices)
    summary = review_svc.get_review_summary(session, session_id, scene_ids=scene_ids)
    states = review_repo.list_by_session(session, session_id)
    warnings: list[str] = []
    if summary.pending > 0:
        warnings.append(f"{summary.pending} escenas pendientes de revisión")
    return summary_to_out(summary, states, warnings=warnings)
