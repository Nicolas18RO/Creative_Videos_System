"""Rutas REST Fase 6.7.X — override humano de categoría editorial."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from aicos.database.db import session_scope
from aicos.models.schemas import (
    EditorialCategoryOverrideOut,
    EditorialCategoryOverrideSetIn,
)
from aicos.services.editorial_semantic_intent_factory import build_editorial_semantic_intent_service
from aicos.services.editorial_training_factory import build_editorial_training_workspace_service

router = APIRouter()


def _override_out(row) -> EditorialCategoryOverrideOut:
    return EditorialCategoryOverrideOut(
        session_id=row.session_id,
        scene_index=row.scene_index,
        auto_narrative_role=row.auto_narrative_role,
        human_narrative_role=row.human_narrative_role,
        effective_narrative_role=row.effective_role,
        has_category_override=bool(row.human_narrative_role),
    )


@router.put("/sessions/{session_id}/scenes/{scene_index}", response_model=EditorialCategoryOverrideOut)
def set_scene_category_override(
    session_id: str,
    scene_index: int,
    body: EditorialCategoryOverrideSetIn,
) -> EditorialCategoryOverrideOut:
    workspace = build_editorial_training_workspace_service()
    semantic_svc = build_editorial_semantic_intent_service()
    try:
        with session_scope() as session:
            s = workspace.get_session(session, session_id)
            if s is None:
                raise HTTPException(status_code=404, detail="editorial_training_session_not_found")
            row_entity = semantic_svc.set_human_narrative_intent(
                session,
                session_id,
                scene_index,
                body.human_narrative_role,
                reviewer=body.reviewer,
            )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return EditorialCategoryOverrideOut(
        session_id=row_entity.session_id,
        scene_index=row_entity.scene_index,
        auto_narrative_role=row_entity.auto_narrative_intent,
        human_narrative_role=row_entity.human_narrative_intent,
        effective_narrative_role=row_entity.effective_narrative_intent,
        has_category_override=row_entity.has_narrative_intent_override,
    )


@router.get("/sessions/{session_id}", response_model=list[EditorialCategoryOverrideOut])
def list_category_overrides(session_id: str) -> list[EditorialCategoryOverrideOut]:
    semantic_svc = build_editorial_semantic_intent_service()
    with session_scope() as session:
        rows = semantic_svc.list_by_session(session, session_id)
    return [
        EditorialCategoryOverrideOut(
            session_id=r.session_id,
            scene_index=r.scene_index,
            auto_narrative_role=r.auto_narrative_intent,
            human_narrative_role=r.human_narrative_intent,
            effective_narrative_role=r.effective_narrative_intent,
            has_category_override=r.has_narrative_intent_override,
        )
        for r in rows
    ]
