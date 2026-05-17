"""Enriquecimiento de DTOs de escena con estado de revisión."""

from __future__ import annotations

from aicos.application.editorial_review.timeline_review_service import EditorialReviewSummary
from aicos.domain.editorial_dataset.entities import TimelineScene
from aicos.domain.editorial_review.entities import EditorialSceneReviewState
from aicos.domain.editorial_review.enums import EditorialSceneReviewStatus
from aicos.domain.editorial_review.scene_merge import scene_id_from_index
from aicos.domain.timeline_visualization.pacing import hook_probability_for_scene
from aicos.models.schemas import EditorialReviewSummaryOut, EditorialSceneReviewStateOut, TimelineSceneViewModel


def _confidence_for_scene(scene: TimelineScene) -> float:
    return float(hook_probability_for_scene(scene))


def review_state_to_out(st: EditorialSceneReviewState) -> EditorialSceneReviewStateOut:
    return EditorialSceneReviewStateOut(
        scene_id=st.scene_id,
        status=st.status,
        reviewed_at=st.reviewed_at.isoformat() if st.reviewed_at else None,
        reviewer=st.reviewer,
        correction_reason=st.correction_reason,
        merged_into_scene_id=st.merged_into_scene_id,
        confidence_override=st.confidence_override,
        notes=st.notes,
    )


def summary_to_out(
    summary: EditorialReviewSummary,
    states: tuple[EditorialSceneReviewState, ...],
    *,
    warnings: list[str] | None = None,
) -> EditorialReviewSummaryOut:
    pending_ids = [s.scene_id for s in states if s.status == EditorialSceneReviewStatus.PENDING]
    return EditorialReviewSummaryOut(
        session_id=summary.session_id,
        total_scenes=summary.total_scenes,
        pending=summary.pending,
        accepted=summary.accepted,
        rejected=summary.rejected,
        merged=summary.merged,
        edited=summary.edited,
        scene_states=[review_state_to_out(s) for s in states],
        pending_scene_ids=pending_ids,
        warnings=warnings or [],
    )


def apply_review_to_scene_card(
    card: TimelineSceneViewModel,
    scene: TimelineScene,
    review: EditorialSceneReviewState | None,
) -> TimelineSceneViewModel:
    st = review.status if review else EditorialSceneReviewStatus.PENDING
    conf = review.confidence_override if review and review.confidence_override is not None else _confidence_for_scene(scene)
    return card.model_copy(
        update={
            "review_status": st,
            "confidence_score": conf,
            "merged_into_scene_id": review.merged_into_scene_id if review else None,
        }
    )


def build_review_lookup(
    states: tuple[EditorialSceneReviewState, ...],
) -> dict[str, EditorialSceneReviewState]:
    return {s.scene_id: s for s in states}


def scene_index_to_id(scene_index: int) -> str:
    return scene_id_from_index(scene_index)
