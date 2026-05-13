"""GET /projects — lista y detalle para el dashboard PyQt6."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from aicos.database.db import session_scope
from aicos.models.schemas import ProjectDetailResponse, ProjectSummary
from aicos.services import project_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=list[ProjectSummary])
def list_projects() -> list[ProjectSummary]:
    with session_scope() as session:
        return project_service.list_projects(session)


@router.get("/{project_id}", response_model=ProjectDetailResponse)
def get_project(project_id: str) -> ProjectDetailResponse:
    with session_scope() as session:
        detail = project_service.get_project_detail(session, project_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return detail
