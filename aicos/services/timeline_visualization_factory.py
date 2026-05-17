"""Factoría Fase 6.8 — timeline visual."""

from __future__ import annotations

from aicos.application.timeline_visualization.timeline_visualization_service import TimelineVisualizationService
from aicos.config import AppConfig, get_config
from aicos.infrastructure.editorial_dataset.sqlite_creative_timeline_repository import SqlCreativeTimelineRepository
from aicos.infrastructure.timeline_visualization.ffmpeg_thumbnail_service import FFmpegThumbnailService
from aicos.infrastructure.timeline_visualization.sql_clip_library_thumbnail_adapter import (
    SqlClipLibraryThumbnailAdapter,
)
from aicos.infrastructure.timeline_visualization.sql_timeline_clip_preview_repository import (
    SqlTimelineClipPreviewRepository,
)


def build_timeline_visualization_service(app_cfg: AppConfig | None = None) -> TimelineVisualizationService:
    cfg = app_cfg or get_config()
    paths = cfg.resolved_paths()
    cache = paths["timeline_visualization_cache"]
    cache.mkdir(parents=True, exist_ok=True)
    media = FFmpegThumbnailService(cfg=cfg.timeline_visualization, cache_root=cache)
    return TimelineVisualizationService(
        cfg=cfg.timeline_visualization,
        timeline_read=SqlCreativeTimelineRepository(),
        preview_repo=SqlTimelineClipPreviewRepository(),
        media_gen=media,
        clip_thumbs=SqlClipLibraryThumbnailAdapter(),
    )
