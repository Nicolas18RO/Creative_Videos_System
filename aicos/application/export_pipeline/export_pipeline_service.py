"""Orquestación de serialización, snapshots y manifests de exportación."""

from __future__ import annotations

import uuid
from dataclasses import replace
from datetime import datetime, timezone
from typing import Any

from aicos.application.export_pipeline.ports import ExportSourcePort, ManifestWriterPort, SnapshotStorePort, TimelineRestorePort
from aicos.domain.export_pipeline.entities import CapCutManifest, ExportManifest, ProjectEditorialBundle
from aicos.domain.export_pipeline.rules import (
    build_capcut_manifest,
    build_export_manifest,
    validate_bundle_for_export,
)


class ExportPipelineService:
    def __init__(
        self,
        *,
        source: ExportSourcePort,
        snapshots: SnapshotStorePort,
        manifests: ManifestWriterPort,
        timeline_restore: TimelineRestorePort,
    ) -> None:
        self._source = source
        self._snapshots = snapshots
        self._manifests = manifests
        self._timeline_restore = timeline_restore

    def get_live_bundle(self, session: Any, project_id: str) -> ProjectEditorialBundle:
        bundle = self._source.load_editorial_bundle(session, project_id)
        if bundle is None:
            raise ValueError("project_not_found")
        return bundle

    def build_capcut_manifest(self, session: Any, project_id: str) -> CapCutManifest:
        bundle = self.get_live_bundle(session, project_id)
        ok, msg = validate_bundle_for_export(bundle)
        if not ok:
            raise ValueError(msg)
        paths = self._source.clip_paths_for_scenes(session, bundle.scenes)
        manifest = build_capcut_manifest(bundle, paths)
        return replace(manifest, generated_at=datetime.now(timezone.utc))

    def build_export_manifest(self, session: Any, project_id: str) -> ExportManifest:
        bundle = self.get_live_bundle(session, project_id)
        ok, msg = validate_bundle_for_export(bundle)
        if not ok:
            raise ValueError(msg)
        paths = self._source.clip_paths_for_scenes(session, bundle.scenes)
        flat = {cid: t[0] for cid, t in paths.items()}
        return build_export_manifest(bundle, flat)

    def persist_snapshot(self, session: Any, project_id: str, *, label: str | None = None) -> tuple[str, str]:
        bundle = self.get_live_bundle(session, project_id)
        ok, msg = validate_bundle_for_export(bundle)
        if not ok:
            raise ValueError(msg)
        sid = uuid.uuid4().hex
        now = datetime.now(timezone.utc)
        stamped = replace(bundle, snapshot_id=sid, created_at=now)
        rel_path = self._snapshots.save_snapshot(stamped, snapshot_id=sid, created_at=now)
        return sid, rel_path

    def list_snapshots(self, project_id: str) -> list[tuple[str, datetime, str]]:
        return self._snapshots.list_snapshots(project_id)

    def load_snapshot(self, project_id: str, snapshot_id: str) -> ProjectEditorialBundle:
        bundle = self._snapshots.load_snapshot(project_id, snapshot_id)
        if bundle is None:
            raise ValueError("snapshot_not_found")
        return bundle

    def restore_snapshot(self, session: Any, project_id: str, snapshot_id: str) -> int:
        bundle = self.load_snapshot(project_id, snapshot_id)
        if bundle.project_id != project_id:
            raise ValueError("snapshot_project_mismatch")
        ok, msg = validate_bundle_for_export(bundle)
        if not ok:
            raise ValueError(msg)
        scenes = self._timeline_restore.replace_timeline_from_bundle(session, project_id, bundle.scenes)
        return len(scenes)

    def write_capcut_manifest_file(self, session: Any, project_id: str) -> str:
        from aicos.application.export_pipeline.presentation import capcut_manifest_to_dict

        manifest = self.build_capcut_manifest(session, project_id)
        payload = capcut_manifest_to_dict(manifest)
        return self._manifests.write_capcut_manifest(project_id, payload)

    def write_export_manifest_file(self, session: Any, project_id: str) -> str:
        from aicos.application.export_pipeline.presentation import export_manifest_to_dict

        manifest = self.build_export_manifest(session, project_id)
        payload = export_manifest_to_dict(manifest)
        return self._manifests.write_export_manifest(project_id, payload)
