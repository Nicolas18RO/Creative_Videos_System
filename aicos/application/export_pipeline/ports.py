"""Puertos del pipeline de exportación."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol

from aicos.domain.export_pipeline.entities import ProjectEditorialBundle
from aicos.domain.cinematic_timeline.entities import ProjectTimelineScene


class ExportSourcePort(Protocol):
    def load_editorial_bundle(self, session: Any, project_id: str) -> ProjectEditorialBundle | None: ...

    def clip_paths_for_scenes(
        self, session: Any, scenes: tuple[Any, ...]
    ) -> dict[str, tuple[str, str, int | None]]: ...


class SnapshotStorePort(Protocol):
    def save_snapshot(self, bundle: ProjectEditorialBundle, *, snapshot_id: str, created_at: datetime) -> str: ...

    def list_snapshots(self, project_id: str) -> list[tuple[str, datetime, str]]: ...

    def load_snapshot(self, project_id: str, snapshot_id: str) -> ProjectEditorialBundle | None: ...


class ManifestWriterPort(Protocol):
    def write_capcut_manifest(self, project_id: str, payload: dict) -> str: ...

    def write_export_manifest(self, project_id: str, payload: dict) -> str: ...


class TimelineRestorePort(Protocol):
    def replace_timeline_from_bundle(
        self, session: Any, project_id: str, scenes: tuple[ExportTimelineScene, ...]
    ) -> tuple[ProjectTimelineScene, ...]: ...
