"""POST /human-feedback — ingestión de señales editoriales humanas (Fase 6.6)."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from aicos.application.human_feedback.human_feedback_reinforcement_service import (
    HumanFeedbackReinforcementService,
    IngestEditorialHumanFeedbackCommand,
)
from aicos.config import get_config
from aicos.database.db import session_scope
from aicos.models.schemas import EditorialHumanFeedbackIngestRequest, EditorialHumanFeedbackIngestResponse
from aicos.services.human_feedback_reinforcement_factory import build_human_feedback_reinforcement_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/events", response_model=EditorialHumanFeedbackIngestResponse)
def post_editorial_human_feedback_event(body: EditorialHumanFeedbackIngestRequest) -> EditorialHumanFeedbackIngestResponse:
    cfg = get_config()
    if not cfg.human_feedback_reinforcement.enabled:
        raise HTTPException(status_code=404, detail="human_feedback_reinforcement_disabled")
    svc: HumanFeedbackReinforcementService = build_human_feedback_reinforcement_service(cfg)
    cmd = IngestEditorialHumanFeedbackCommand(
        event_kind=body.event_kind,
        reward=body.reward,
        creative_id=body.creative_id,
        clip_id=body.clip_id,
        replaced_clip_id=body.replaced_clip_id,
        scene_index=body.scene_index,
        narrative_function=body.narrative_function,
        transition_type=body.transition_type,
        query_fingerprint=body.query_fingerprint,
    )
    try:
        with session_scope() as session:
            eid = svc.ingest(session, cmd)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.exception("[HumanFeedbackReinforcement] ingest_failed")
        raise HTTPException(status_code=500, detail=str(e)) from e
    return EditorialHumanFeedbackIngestResponse(event_id=eid)
