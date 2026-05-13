"""API fina: inteligencia cinematográfica (delegación en capa application)."""

from __future__ import annotations

import logging

from fastapi import APIRouter

from aicos.models.schemas import (
    CinematicEmotionBlock,
    CinematicNarrativeBlock,
    CinematicSceneTextRequest,
    CinematicSceneTextResponse,
    CinematicVisualIntentBlock,
)
from aicos.services import cinematic_intel_factory

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/scene-text", response_model=CinematicSceneTextResponse)
def analyze_scene_text(body: CinematicSceneTextRequest) -> CinematicSceneTextResponse:
    """Clasificación narrativa, emoción e intención visual solo desde texto (local-first)."""
    narr = cinematic_intel_factory.build_narrative_classifier_service()
    emo = cinematic_intel_factory.build_emotion_analysis_service()
    vis = cinematic_intel_factory.build_visual_intent_extraction_service()
    n_out, prov = narr.classify(body.transcript, body.scene_text, body.context)
    e_out = emo.analyze(
        body.transcript,
        body.scene_text,
        pacing_hint=n_out.pacing_recommendation,
    )
    intents = vis.extract(body.transcript, body.scene_text)
    logger.info("cinematic_intel api=scene-text narrative=%s emotion=%s", n_out.narrative_role.value, e_out.primary_emotion.value)
    return CinematicSceneTextResponse(
        narrative=CinematicNarrativeBlock(
            narrative_role=n_out.narrative_role.value,
            confidence=n_out.confidence,
            reasoning=n_out.reasoning,
            compatible_visual_styles=list(n_out.compatible_visual_styles),
            pacing_recommendation=n_out.pacing_recommendation,
            provider_used=prov,
        ),
        emotion=CinematicEmotionBlock(
            primary_emotion=e_out.primary_emotion.value,
            secondary_emotions=[x.value for x in e_out.secondary_emotions],
            emotional_intensity=e_out.emotional_intensity,
            emotional_arc_position=e_out.emotional_arc_position,
            energy_curve=e_out.energy_curve,
            emotional_transition=e_out.emotional_transition,
        ),
        visual_intents=[
            CinematicVisualIntentBlock(
                intent_type=v.intent_type.value,
                cinematic_priority=v.cinematic_priority,
                suggested_camera_styles=list(v.suggested_camera_styles),
                suggested_editing_styles=list(v.suggested_editing_styles),
                suggested_visual_elements=list(v.suggested_visual_elements),
                suggested_motion=list(v.suggested_motion),
                suggested_color_mood=list(v.suggested_color_mood),
                suggested_transition_style=list(v.suggested_transition_style),
                suggested_shot_types=list(v.suggested_shot_types),
            )
            for v in intents
        ],
    )
