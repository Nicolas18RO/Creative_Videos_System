"""GET /gaps/{project_id} — gaps persistidos de un proyecto."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from aicos.database.db import ProjectRow, session_scope
from aicos.models.schemas import ProjectGapsResponse
from aicos.services import project_service

router = APIRouter()


@router.get("/{project_id}", response_model=ProjectGapsResponse)
def get_gaps(project_id: str) -> ProjectGapsResponse:
    """Devuelve la lista de gaps asociados a las escenas del proyecto."""
    with session_scope() as session:
        if session.get(ProjectRow, project_id) is None:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")
        return project_service.get_project_gaps(session, project_id)
