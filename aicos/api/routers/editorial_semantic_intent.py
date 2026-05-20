"""Rutas REST — capa de intención semántica editorial (Fase 6.7.X)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from aicos.database.db import session_scope
from aicos.domain.editorial_taxonomy.entities import SceneSemanticIntent
from aicos.models.schemas import EditorialSemanticIntentOut, EditorialSemanticIntentPatchIn
from aicos.services.editorial_semantic_intent_factory import build_editorial_semantic_intent_service
from aicos.services.editorial_training_factory import build_editorial_training_workspace_service

router = APIRouter()


def _intent_out(row: SceneSemanticIntent) -> EditorialSemanticIntentOut:
    return EditorialSemanticIntentOut(
        session_id=row.session_id,
        scene_index=row.scene_index,
        clip_id=row.clip_id,
        clip_source_taxonomy=row.effective_clip_source,
        auto_clip_source_taxonomy=row.auto_clip_source_taxonomy,
        human_clip_source_taxonomy=row.human_clip_source_taxonomy,
        narrative_intent=row.effective_narrative_intent,
        auto_narrative_intent=row.auto_narrative_intent,
        human_narrative_intent=row.human_narrative_intent,
        emotional_intent=row.effective_emotional_intent,
        auto_emotional_intent=row.auto_emotional_intent,
        human_emotional_intent=row.human_emotional_intent,
        audio_fragment_text=row.audio_fragment_text,
        visual_style_label=row.visual_style_label,
        has_narrative_intent_override=row.has_narrative_intent_override,
        has_clip_taxonomy_override=row.has_clip_taxonomy_override,
    )


@router.patch("/sessions/{session_id}/scenes/{scene_index}", response_model=EditorialSemanticIntentOut)
def patch_scene_semantic_intent(
    session_id: str,
    scene_index: int,
    body: EditorialSemanticIntentPatchIn,
) -> EditorialSemanticIntentOut:
    workspace = build_editorial_training_workspace_service()
    svc = build_editorial_semantic_intent_service()
    try:
        with session_scope() as session:
            if workspace.get_session(session, session_id) is None:
                raise HTTPException(status_code=404, detail="editorial_training_session_not_found")
            row: SceneSemanticIntent | None = svc.get_for_scene(session, session_id, scene_index)
            if body.human_narrative_intent is not None:
                row = svc.set_human_narrative_intent(
                    session,
                    session_id,
                    scene_index,
                    body.human_narrative_intent,
                    reviewer=body.reviewer,
                )
            if body.human_clip_source_taxonomy is not None:
                row = svc.set_human_clip_source_taxonomy(
                    session,
                    session_id,
                    scene_index,
                    body.human_clip_source_taxonomy,
                    reviewer=body.reviewer,
                )
            if body.human_emotional_intent is not None:
                row = svc.set_human_emotional_intent(
                    session,
                    session_id,
                    scene_index,
                    body.human_emotional_intent,
                    reviewer=body.reviewer,
                )
            if row is None:
                raise HTTPException(status_code=404, detail="semantic_intent_not_found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return _intent_out(row)


@router.get("/sessions/{session_id}", response_model=list[EditorialSemanticIntentOut])
def list_semantic_intents(session_id: str) -> list[EditorialSemanticIntentOut]:
    svc = build_editorial_semantic_intent_service()
    with session_scope() as session:
        rows = svc.list_by_session(session, session_id)
    return [_intent_out(r) for r in rows]
