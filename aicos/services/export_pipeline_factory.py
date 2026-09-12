"""Factory del pipeline de exportación (Phase 7.4)."""

from __future__ import annotations

from aicos.application.export_pipeline.export_pipeline_service import ExportPipelineService
from aicos.application.export_pipeline.studio_analyze_upload_service import StudioAnalyzeUploadService
from aicos.config import get_config
from aicos.infrastructure.export_pipeline.filesystem_manifest_writer import FilesystemManifestWriter
from aicos.infrastructure.export_pipeline.filesystem_snapshot_store import FilesystemSnapshotStore
from aicos.infrastructure.export_pipeline.sql_export_source_repository import SqlExportSourceRepository
from aicos.infrastructure.export_pipeline.timeline_restore_adapter import TimelineRestoreAdapter


def build_export_pipeline_service() -> ExportPipelineService:
    paths = get_config().resolved_paths()
    exports = paths["exports"]
    return ExportPipelineService(
        source=SqlExportSourceRepository(),
        snapshots=FilesystemSnapshotStore(exports),
        manifests=FilesystemManifestWriter(exports),
        timeline_restore=TimelineRestoreAdapter(),
    )


def build_studio_analyze_upload_service() -> StudioAnalyzeUploadService:
    paths = get_config().resolved_paths()
    cache = paths["exports"].parent / "cache" / "studio_audio"
    return StudioAnalyzeUploadService(cache_root=cache, max_upload_mb=256)
