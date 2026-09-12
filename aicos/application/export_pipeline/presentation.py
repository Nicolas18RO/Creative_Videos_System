"""Mapeo dominio → contratos API de exportación."""

from __future__ import annotations

from datetime import datetime

from aicos.domain.export_pipeline.entities import CapCutManifest, ExportManifest, ProjectEditorialBundle
from aicos.models.schemas import (
    CapCutManifestOut,
    CapCutTrackEntryOut,
    ExportAssetDependencyOut,
    ExportManifestEntryOut,
    ExportManifestOut,
    ProjectEditorialBundleOut,
    ProjectSnapshotMetaOut,
    ProjectSnapshotOut,
    ExportTimelineSceneOut,
)


def _dt_iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    return dt.isoformat()


def bundle_to_out(bundle: ProjectEditorialBundle) -> ProjectEditorialBundleOut:
    return ProjectEditorialBundleOut(
        format_version=bundle.format_version,
        project_id=bundle.project_id,
        project_name=bundle.project_name,
        status=bundle.status,
        audio_file_path=bundle.audio_file_path,
        transcript_path=bundle.transcript_path,
        product_name=bundle.product_name,
        product_category=bundle.product_category,
        target_audience=bundle.target_audience,
        snapshot_id=bundle.snapshot_id,
        created_at=_dt_iso(bundle.created_at),
        scenes=[
            ExportTimelineSceneOut(
                scene_id=s.scene_id,
                scene_index=s.scene_index,
                start_ms=s.start_ms,
                end_ms=s.end_ms,
                duration_ms=s.duration_ms,
                text=s.text,
                concept=s.concept,
                narrative_function=s.narrative_function,
                selected_clip_id=s.selected_clip_id,
                is_hook=s.is_hook,
            )
            for s in bundle.scenes
        ],
        assets=[
            ExportAssetDependencyOut(
                clip_id=a.clip_id,
                absolute_path=a.absolute_path,
                exists_on_disk=a.exists_on_disk,
                duration_ms=a.duration_ms,
                filename=a.filename,
            )
            for a in bundle.assets
        ],
    )


def capcut_manifest_to_dict(manifest: CapCutManifest) -> dict:
    return capcut_manifest_to_out(manifest).model_dump(mode="json")


def export_manifest_to_dict(manifest: ExportManifest) -> dict:
    return export_manifest_to_out(manifest).model_dump(mode="json")


def capcut_manifest_to_out(manifest: CapCutManifest) -> CapCutManifestOut:
    return CapCutManifestOut(
        format_version=manifest.format_version,
        project_id=manifest.project_id,
        project_name=manifest.project_name,
        audio_master_path=manifest.audio_master_path,
        timeline_duration_ms=manifest.timeline_duration_ms,
        generated_at=_dt_iso(manifest.generated_at),
        warnings=list(manifest.warnings),
        entries=[
            CapCutTrackEntryOut(
                order=e.order,
                scene_id=e.scene_id,
                scene_index=e.scene_index,
                timeline_start_ms=e.timeline_start_ms,
                timeline_end_ms=e.timeline_end_ms,
                duration_ms=e.duration_ms,
                clip_id=e.clip_id,
                clip_path=e.clip_path,
                clip_exists=e.clip_exists,
                text=e.text,
                concept=e.concept,
                narrative_function=e.narrative_function,
            )
            for e in manifest.entries
        ],
        asset_dependencies=[
            ExportAssetDependencyOut(
                clip_id=a.clip_id,
                absolute_path=a.absolute_path,
                exists_on_disk=a.exists_on_disk,
                duration_ms=a.duration_ms,
                filename=a.filename,
            )
            for a in manifest.asset_dependencies
        ],
    )


def export_manifest_to_out(manifest: ExportManifest) -> ExportManifestOut:
    return ExportManifestOut(
        format_version=manifest.format_version,
        project_id=manifest.project_id,
        project_name=manifest.project_name,
        timeline_duration_ms=manifest.timeline_duration_ms,
        audio_path=manifest.audio_path,
        missing_assets=list(manifest.missing_assets),
        entries=[
            ExportManifestEntryOut(
                scene_id=e.scene_id,
                scene_index=e.scene_index,
                start_ms=e.start_ms,
                end_ms=e.end_ms,
                clip_id=e.clip_id,
                clip_path=e.clip_path,
                clip_ready=e.clip_ready,
            )
            for e in manifest.entries
        ],
    )


def snapshot_meta_list(items: list[tuple[str, datetime, str]]) -> list[ProjectSnapshotMetaOut]:
    return [
        ProjectSnapshotMetaOut(
            snapshot_id=sid,
            created_at=dt.isoformat(),
            path=path,
        )
        for sid, dt, path in items
    ]


def snapshot_to_out(bundle: ProjectEditorialBundle) -> ProjectSnapshotOut:
    return ProjectSnapshotOut(bundle=bundle_to_out(bundle))
