"""Factoría de servicios editoriales (Fase 5.3)."""

from __future__ import annotations

from aicos.application.editorial_metadata.editorial_feedback_service import EditorialFeedbackService
from aicos.application.editorial_metadata.editorial_metadata_service import EditorialMetadataService
from aicos.config import AppConfig, get_config
from aicos.infrastructure.editorial_metadata.sql_editorial_feedback_repository import (
    SqlEditorialFeedbackRepository,
)
from aicos.infrastructure.editorial_metadata.sql_editorial_metadata_repository import (
    SqlEditorialMetadataRepository,
)


def build_editorial_metadata_service(app_cfg: AppConfig | None = None) -> EditorialMetadataService:
    cfg = app_cfg or get_config()
    repo = SqlEditorialMetadataRepository()
    return EditorialMetadataService(
        read_port=repo,
        write_port=repo,
        cfg=cfg.editorial_metadata,
    )


def build_editorial_feedback_service(app_cfg: AppConfig | None = None) -> EditorialFeedbackService:
    cfg = app_cfg or get_config()
    return EditorialFeedbackService(
        write_port=SqlEditorialFeedbackRepository(),
        cfg=cfg.editorial_metadata,
    )
