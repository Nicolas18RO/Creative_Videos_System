"""Entidades del pipeline de exportación y serialización de proyectos."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


BUNDLE_FORMAT_VERSION = "aicos-project-bundle-v1"
CAPCUT_MANIFEST_FORMAT = "aicos-capcut-manifest-v1"
EXPORT_MANIFEST_FORMAT = "aicos-export-manifest-v1"


@dataclass(frozen=True, slots=True)
class ExportTimelineScene:
    scene_id: str
    scene_index: int
    start_ms: int
    end_ms: int
    duration_ms: int
    text: str
    concept: str
    narrative_function: str
    selected_clip_id: str | None
    is_hook: bool = False


@dataclass(frozen=True, slots=True)
class ExportAssetDependency:
    clip_id: str
    absolute_path: str
    exists_on_disk: bool
    duration_ms: int | None = None
    filename: str = ""


@dataclass(frozen=True, slots=True)
class ProjectEditorialBundle:
    """Estado serializable de un proyecto + timeline para snapshots y restauración."""

    project_id: str
    project_name: str
    status: str
    audio_file_path: str | None
    transcript_path: str | None
    product_name: str | None
    product_category: str | None
    target_audience: str | None
    scenes: tuple[ExportTimelineScene, ...]
    assets: tuple[ExportAssetDependency, ...]
    format_version: str = BUNDLE_FORMAT_VERSION
    snapshot_id: str | None = None
    created_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class CapCutTrackEntry:
    order: int
    scene_id: str
    scene_index: int
    timeline_start_ms: int
    timeline_end_ms: int
    duration_ms: int
    clip_id: str | None
    clip_path: str | None
    clip_exists: bool
    text: str
    concept: str
    narrative_function: str


@dataclass(frozen=True, slots=True)
class CapCutManifest:
    project_id: str
    project_name: str
    audio_master_path: str | None
    timeline_duration_ms: int
    format_version: str = CAPCUT_MANIFEST_FORMAT
    generated_at: datetime | None = None
    entries: tuple[CapCutTrackEntry, ...] = ()
    asset_dependencies: tuple[ExportAssetDependency, ...] = ()
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ExportManifestEntry:
    scene_id: str
    scene_index: int
    start_ms: int
    end_ms: int
    clip_id: str | None
    clip_path: str | None
    clip_ready: bool


@dataclass(frozen=True, slots=True)
class ExportManifest:
    project_id: str
    project_name: str
    format_version: str = EXPORT_MANIFEST_FORMAT
    timeline_duration_ms: int = 0
    audio_path: str | None = None
    entries: tuple[ExportManifestEntry, ...] = ()
    missing_assets: tuple[str, ...] = ()
