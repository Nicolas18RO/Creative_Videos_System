"""Factory del timeline de proyecto (Phase 7.2)."""

from __future__ import annotations

from aicos.application.cinematic_timeline.project_timeline_service import ProjectTimelineService
from aicos.infrastructure.cinematic_timeline.sql_project_timeline_repository import (
    SqlProjectTimelineRepository,
)


def build_project_timeline_service() -> ProjectTimelineService:
    return ProjectTimelineService(persistence=SqlProjectTimelineRepository())
