"""Rutas REST Fase 6.7.1 — revisión editorial humana (orquestación fina)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from aicos.application.editorial_dataset.ports import CreativeTimelinePersistenceReadPort
from aicos.application.editorial_review.presentation import review_state_to_out, summary_to_out
from aicos.application.editorial_review.workspace_integration import load_review_summary_for_session
from aicos.application.editorial_review.timeline_review_service import TimelineReviewService
from aicos.application.editorial_training.editorial_training_views import build_timeline_scene_cards
from aicos.application.human_feedback.human_feedback_reinforcement_service import (
    HumanFeedbackReinforcementService,
    IngestEditorialHumanFeedbackCommand,
)
from aicos.config import get_config
from aicos.database.db import session_scope
from aicos.domain.editorial_review.enums import EditorialSceneReviewStatus
from aicos.domain.editorial_review.scene_merge import scene_id_from_index
from aicos.models.schemas import (
    EditorialBulkActionIn,
    EditorialReviewSummaryOut,
    EditorialSceneBulkStatusIn,
    EditorialSceneMergeIn,
    EditorialSceneReviewStateOut,
    EditorialSceneReviewStatusIn,
)
from aicos.services.editorial_semantic_intent_factory import build_editorial_semantic_intent_service
from aicos.services.editorial_review_factory import (
    build_bulk_review_service,
    build_merge_scenes_service,
    build_timeline_review_service,
)
from aicos.services.editorial_training_factory import build_editorial_training_workspace_service
from aicos.infrastructure.editorial_dataset.sqlite_creative_timeline_repository import SqlCreativeTimelineRepository
from aicos.infrastructure.editorial_review.sql_editorial_scene_review_repository import (
    SqlEditorialSceneReviewRepository,
)
from aicos.services.human_feedback_reinforcement_factory import build_human_feedback_reinforcement_service

router = APIRouter()


def _maybe_ingest_feedback(
    session,
    *,
    session_id: str,
    scene_id: str,
    status: str,
    body: EditorialSceneReviewStatusIn,
    creative_id: str | None,
) -> None:
    if not body.ingest_feedback:
        return
    cfg = get_config()
    if not cfg.human_feedback_reinforcement.enabled:
        return
    hf = build_human_feedback_reinforcement_service(cfg)
    if hf is None:
        return
    reward = 1.0 if status == EditorialSceneReviewStatus.ACCEPTED else -0.6 if status == EditorialSceneReviewStatus.REJECTED else 0.0
    if status not in (EditorialSceneReviewStatus.ACCEPTED, EditorialSceneReviewStatus.REJECTED):
        return
    kind = "clip_accept" if status == EditorialSceneReviewStatus.ACCEPTED else "clip_reject"
    try:
        scene_index = int(scene_id)
    except ValueError:
        scene_index = None
    hf.ingest(
        session,
        IngestEditorialHumanFeedbackCommand(
            event_kind=kind,
            reward=reward,
            creative_id=creative_id,
            clip_id=body.clip_id,
            scene_index=scene_index,
            narrative_function=body.narrative_function,
            transition_type=body.transition_type,
            query_fingerprint=None,
        ),
    )


def _load_scene_indices(timeline_read: CreativeTimelinePersistenceReadPort, session, creative_id: str) -> tuple[int, ...]:
    tl = timeline_read.get_by_creative_id(session, creative_id)
    if tl is None:
        return ()
    return tuple(s.scene_index for s in tl.timeline_scenes)


def _full_summary(session, session_id: str, creative_id: str) -> EditorialReviewSummaryOut:
    out = load_review_summary_for_session(
        session,
        session_id,
        creative_id,
        timeline_read=SqlCreativeTimelineRepository(),
        review_svc=build_timeline_review_service(),
        review_repo=SqlEditorialSceneReviewRepository(),
    )
    if out is None:
        raise HTTPException(status_code=404, detail="creative_timeline_not_found")
    return out


@router.post("/scenes/{scene_id}/status", response_model=EditorialSceneReviewStateOut)
def set_scene_review_status(scene_id: str, body: EditorialSceneReviewStatusIn) -> EditorialSceneReviewStateOut:
    review_svc = build_timeline_review_service()
    workspace = build_editorial_training_workspace_service()
    try:
        with session_scope() as session:
            s = workspace.get_session(session, body.session_id)
            if s is None:
                raise HTTPException(status_code=404, detail="editorial_training_session_not_found")
            st = review_svc.set_scene_status(
                session,
                body.session_id,
                scene_id,
                status=body.status,
                reviewer=body.reviewer,
                correction_reason=body.correction_reason,
                notes=body.notes,
                confidence_override=body.confidence_override,
            )
            if body.narrative_function:
                try:
                    build_editorial_semantic_intent_service().set_human_narrative_intent(
                        session,
                        body.session_id,
                        int(scene_id),
                        body.narrative_function,
                        reviewer=body.reviewer,
                    )
                except ValueError:
                    pass
            _maybe_ingest_feedback(
                session,
                session_id=body.session_id,
                scene_id=scene_id,
                status=body.status,
                body=body,
                creative_id=s.creative_id,
            )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return review_state_to_out(st)


@router.post("/scenes/bulk-status", response_model=EditorialReviewSummaryOut)
def bulk_set_scene_status(body: EditorialSceneBulkStatusIn) -> EditorialReviewSummaryOut:
    review_svc = build_timeline_review_service()
    workspace = build_editorial_training_workspace_service()
    try:
        with session_scope() as session:
            s = workspace.get_session(session, body.session_id)
            if s is None:
                raise HTTPException(status_code=404, detail="editorial_training_session_not_found")
            review_svc.batch_set_status(
                session,
                body.session_id,
                tuple(body.scene_ids),
                status=body.status,
                reviewer=body.reviewer,
                correction_reason=body.correction_reason,
            )
            if body.ingest_feedback:
                for sid in body.scene_ids:
                    stub = EditorialSceneReviewStatusIn(
                        session_id=body.session_id,
                        status=body.status,
                        reviewer=body.reviewer,
                        correction_reason=body.correction_reason,
                        ingest_feedback=True,
                    )
                    _maybe_ingest_feedback(
                        session,
                        session_id=body.session_id,
                        scene_id=sid,
                        status=body.status,
                        body=stub,
                        creative_id=s.creative_id,
                    )
            return _full_summary(session, body.session_id, s.creative_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/scenes/merge", response_model=EditorialReviewSummaryOut)
def merge_scenes(body: EditorialSceneMergeIn) -> EditorialReviewSummaryOut:
    merge_svc = build_merge_scenes_service()
    try:
        with session_scope() as session:
            merge_svc.merge_adjacent_scenes(
                session,
                body.session_id,
                body.creative_id,
                body.scene_index_a,
                body.scene_index_b,
                reviewer=body.reviewer,
            )
            return _full_summary(session, body.session_id, body.creative_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/sessions/{session_id}/summary", response_model=EditorialReviewSummaryOut)
def get_review_summary(session_id: str, creative_id: str) -> EditorialReviewSummaryOut:
    with session_scope() as session:
        return _full_summary(session, session_id, creative_id)


@router.post("/sessions/{session_id}/bulk-action", response_model=EditorialReviewSummaryOut)
def bulk_review_action(session_id: str, body: EditorialBulkActionIn) -> EditorialReviewSummaryOut:
    bulk = build_bulk_review_service()
    timeline_read = SqlCreativeTimelineRepository()
    review_repo = SqlEditorialSceneReviewRepository()
    try:
        with session_scope() as session:
            indices = _load_scene_indices(timeline_read, session, body.creative_id)
            action = (body.action or "").strip().lower()
            if action == "accept_all_pending":
                summary = bulk.accept_all_pending(session, session_id, indices)
            elif action == "reject_all_pending":
                summary = bulk.reject_all_pending(session, session_id, indices)
            elif action == "reset_review_states":
                summary = bulk.reset_review_states(session, session_id, indices)
            elif action == "accept_high_confidence":
                tl = timeline_read.get_by_creative_id(session, body.creative_id)
                conf: dict[str, float] = {}
                if tl:
                    from aicos.domain.timeline_visualization.pacing import hook_probability_for_scene

                    for sc in tl.timeline_scenes:
                        conf[scene_id_from_index(sc.scene_index)] = hook_probability_for_scene(sc)
                summary = bulk.auto_accept_high_confidence(
                    session,
                    session_id,
                    indices,
                    confidence_by_scene=conf,
                    threshold=body.confidence_threshold,
                )
            else:
                raise HTTPException(status_code=400, detail="unknown_bulk_action")
            states = review_repo.list_by_session(session, session_id)
            return summary_to_out(summary, states)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
