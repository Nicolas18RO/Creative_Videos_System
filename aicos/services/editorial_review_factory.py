"""Factoría Fase 6.7.1 — revisión editorial humana."""

from __future__ import annotations

from typing import Any

from aicos.application.editorial_review.bulk_review_service import BulkReviewService
from aicos.application.editorial_review.merge_scenes_service import MergeScenesService
from aicos.application.editorial_review.timeline_review_service import TimelineReviewService
from aicos.application.editorial_training.editorial_training_workspace_service import EditorialTrainingWorkspaceService
from aicos.config import AppConfig, get_config
from aicos.infrastructure.editorial_dataset.sqlite_creative_timeline_repository import SqlCreativeTimelineRepository
from aicos.infrastructure.editorial_review.sql_editorial_scene_review_repository import (
    SqlEditorialSceneMergeRepository,
    SqlEditorialSceneReviewRepository,
)
from aicos.services.editorial_training_factory import build_editorial_training_workspace_service


def _submit_timeline_adapter(workspace: EditorialTrainingWorkspaceService):
    def submit(
        session: Any,
        session_id: str,
        creative_id: str,
        raw: tuple,
        audio_path: str,
        final_video_path: str,
    ):
        s = workspace.get_session(session, session_id)
        if s is None:
            raise ValueError("editorial_training_session_not_found")
        return workspace.submit_timeline(session, session_id, raw)

    return submit


def build_timeline_review_service(app_cfg: AppConfig | None = None) -> TimelineReviewService:
    return TimelineReviewService(persistence=SqlEditorialSceneReviewRepository())


def build_bulk_review_service(app_cfg: AppConfig | None = None) -> BulkReviewService:
    return BulkReviewService(review=build_timeline_review_service(app_cfg))


def build_merge_scenes_service(app_cfg: AppConfig | None = None) -> MergeScenesService:
    cfg = app_cfg or get_config()
    workspace = build_editorial_training_workspace_service(cfg)
    from aicos.services.editorial_semantic_intent_factory import build_editorial_semantic_intent_service

    semantic = build_editorial_semantic_intent_service(cfg)

    def _semantic_merge(session, session_id, **kwargs):
        semantic.merge_semantic_intents_after_scene_merge(session, session_id, **kwargs)

    return MergeScenesService(
        timeline_read=SqlCreativeTimelineRepository(),
        timeline_write=SqlCreativeTimelineRepository(),
        review=build_timeline_review_service(cfg),
        review_repo=SqlEditorialSceneReviewRepository(),
        merge_repo=SqlEditorialSceneMergeRepository(),
        timeline_builder_submit=_submit_timeline_adapter(workspace),
        semantic_intent_merge=_semantic_merge,
    )
