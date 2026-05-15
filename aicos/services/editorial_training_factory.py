"""Factoría Fase 6.7 — workspace de entrenamiento editorial."""

from __future__ import annotations

from aicos.application.editorial_training.editorial_training_analyze_service import EditorialTrainingAnalyzeService
from aicos.application.editorial_training.editorial_training_upload_service import EditorialTrainingUploadService
from aicos.application.editorial_training.editorial_training_workspace_service import EditorialTrainingWorkspaceService
from aicos.config import AppConfig, get_config
from aicos.infrastructure.editorial_dataset.ffmpeg_metadata_adapter import FfmpegVideoMetadataAdapter
from aicos.infrastructure.editorial_dataset.sqlite_creative_timeline_repository import SqlCreativeTimelineRepository
from aicos.infrastructure.editorial_training.delegate_style_embedding_attach import (
    ServiceEditorialStyleEmbeddingAttachAdapter,
)
from aicos.infrastructure.editorial_training.sql_editorial_training_session_repository import (
    SqlEditorialTrainingSessionRepository,
)
from aicos.services.editorial_dataset_factory import build_creative_timeline_builder_service
from aicos.services.human_feedback_reinforcement_factory import build_human_feedback_reinforcement_service


def build_editorial_training_workspace_service(app_cfg: AppConfig | None = None) -> EditorialTrainingWorkspaceService:
    cfg = app_cfg or get_config()
    hf = None
    if cfg.human_feedback_reinforcement.enabled:
        hf = build_human_feedback_reinforcement_service(cfg)
    return EditorialTrainingWorkspaceService(
        workspace_cfg=cfg.editorial_training_workspace,
        app_cfg=cfg,
        persistence=SqlEditorialTrainingSessionRepository(),
        timeline_builder=build_creative_timeline_builder_service(cfg, with_persistence=True),
        timeline_read=SqlCreativeTimelineRepository(),
        human_feedback=hf,
        style_embedding_attach=ServiceEditorialStyleEmbeddingAttachAdapter(cfg),
    )


def build_editorial_training_upload_service(app_cfg: AppConfig | None = None) -> EditorialTrainingUploadService:
    cfg = app_cfg or get_config()
    paths = cfg.resolved_paths()
    root = paths["editorial_training_uploads"]
    root.mkdir(parents=True, exist_ok=True)
    return EditorialTrainingUploadService(
        workspace_cfg=cfg.editorial_training_workspace,
        uploads_root=root,
        media_probe=FfmpegVideoMetadataAdapter(),
    )


def build_editorial_training_analyze_service(app_cfg: AppConfig | None = None) -> EditorialTrainingAnalyzeService:
    cfg = app_cfg or get_config()
    return EditorialTrainingAnalyzeService(
        workspace=build_editorial_training_workspace_service(cfg),
        workspace_cfg=cfg.editorial_training_workspace,
    )