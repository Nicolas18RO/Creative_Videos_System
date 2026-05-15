"""POST /feedback — persistir aceptación/rechazo de recomendaciones."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from aicos.database.db import SceneRow, session_scope
from aicos.models.schemas import FeedbackRequest, FeedbackResponse
from aicos.services import project_service
from aicos.services import prompt_intelligence_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=FeedbackResponse)
def post_feedback(body: FeedbackRequest) -> FeedbackResponse:
    """Actualiza la fila `recommendations` y opcionalmente `scenes.selected_clip_id`."""
    with session_scope() as session:
        n = project_service.update_recommendation_feedback(
            session,
            scene_id=body.scene_id,
            clip_id=body.clip_id,
            accepted=body.accepted,
            rank=body.rank,
        )
        if n > 0:
            scene = session.get(SceneRow, body.scene_id)
            if scene is not None:
                prompt_intelligence_service.record_feedback_event(
                    session,
                    scene_id=body.scene_id,
                    project_id=scene.project_id,
                    clip_id=body.clip_id,
                    accepted=body.accepted,
                    rank=body.rank,
                    narrative_function=scene.narrative_function,
                )
                if body.record_editorial_human_feedback:
                    from aicos.config import get_config as _gf
                    from aicos.application.human_feedback.human_feedback_reinforcement_service import (
                        IngestEditorialHumanFeedbackCommand,
                    )
                    from aicos.services.human_feedback_reinforcement_factory import (
                        build_human_feedback_reinforcement_service,
                    )

                    _cfg = _gf()
                    if _cfg.human_feedback_reinforcement.enabled:
                        hf = build_human_feedback_reinforcement_service(_cfg)
                        rk = 1.0 if body.accepted else -1.0
                        kind = "clip_accept" if body.accepted else "clip_reject"
                        hf.ingest(
                            session,
                            IngestEditorialHumanFeedbackCommand(
                                event_kind=kind,
                                reward=rk,
                                creative_id=None,
                                clip_id=body.clip_id,
                                replaced_clip_id=None,
                                scene_index=scene.scene_index,
                                narrative_function=scene.narrative_function,
                                transition_type=None,
                                query_fingerprint=None,
                            ),
                        )
    if n == 0:
        raise HTTPException(
            status_code=404,
            detail="No hay recomendación para esa escena y clip_id (revisa rank o persistencia del análisis).",
        )
    return FeedbackResponse(updated=n, scene_id=body.scene_id, clip_id=body.clip_id)
