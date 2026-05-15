"""Factoría Fase 6.1 — datasets editoriales (wiring infraestructura ↔ aplicación)."""

from __future__ import annotations

from aicos.application.editorial_dataset.creative_dataset_export_service import CreativeDatasetExportService
from aicos.application.editorial_dataset.creative_timeline_builder_service import CreativeTimelineBuilderService
from aicos.application.editorial_dataset.editorial_pattern_extraction_service import (
    EditorialPatternExtractionService,
)
from aicos.config import AppConfig, get_config
from aicos.infrastructure.editorial_dataset.dataset_file_writer import LocalDatasetFileWriter
from aicos.infrastructure.editorial_dataset.ffmpeg_metadata_adapter import FfmpegVideoMetadataAdapter
from aicos.infrastructure.editorial_dataset.filesystem_adapter import LocalFilesystemAdapter
from aicos.infrastructure.editorial_dataset.json_timeline_reader import JsonTimelineFileReader
from aicos.infrastructure.editorial_dataset.sqlite_creative_timeline_repository import (
    SqlCreativeTimelineRepository,
)


def build_editorial_pattern_extraction_service(app_cfg: AppConfig | None = None) -> EditorialPatternExtractionService:
    cfg = app_cfg or get_config()
    return EditorialPatternExtractionService(cfg.editorial_dataset, cfg.editorial_pattern_engine)


def build_creative_timeline_builder_service(
    app_cfg: AppConfig | None = None,
    *,
    with_persistence: bool = True,
) -> CreativeTimelineBuilderService:
    cfg = app_cfg or get_config()
    ed = cfg.editorial_dataset
    repo = SqlCreativeTimelineRepository() if with_persistence else None
    return CreativeTimelineBuilderService(
        cfg=ed,
        fs=LocalFilesystemAdapter(),
        json_reader=JsonTimelineFileReader(),
        video_probe=FfmpegVideoMetadataAdapter(),
        pattern_service=build_editorial_pattern_extraction_service(cfg),
        persistence=repo,
    )


def build_creative_dataset_export_service(app_cfg: AppConfig | None = None) -> CreativeDatasetExportService:
    cfg = app_cfg or get_config()
    return CreativeDatasetExportService(cfg=cfg.editorial_dataset, writer=LocalDatasetFileWriter())
