"""Reglas puras: validación, manifest CapCut y dependencias de assets."""

from __future__ import annotations

from pathlib import Path

from aicos.domain.export_pipeline.entities import (
    BUNDLE_FORMAT_VERSION,
    CapCutManifest,
    CapCutTrackEntry,
    ExportAssetDependency,
    ExportManifest,
    ExportManifestEntry,
    ExportTimelineScene,
    ProjectEditorialBundle,
)


def bundle_timeline_duration_ms(scenes: tuple[ExportTimelineScene, ...]) -> int:
    if not scenes:
        return 0
    return max(s.end_ms for s in scenes)


def validate_bundle_for_export(bundle: ProjectEditorialBundle) -> tuple[bool, str]:
    if not bundle.project_id.strip():
        return False, "project_id_required"
    if bundle.format_version != BUNDLE_FORMAT_VERSION:
        return False, "unsupported_bundle_version"
    if not bundle.scenes:
        return False, "timeline_empty"
    ordered = sorted(bundle.scenes, key=lambda s: s.scene_index)
    for i, s in enumerate(ordered):
        if s.scene_index != i:
            return False, "scene_index_gap"
        if s.end_ms <= s.start_ms:
            return False, f"invalid_scene_timing:{s.scene_id}"
    return True, "ok"


def _path_exists(p: str | None) -> bool:
    if not p:
        return False
    try:
        return Path(p).expanduser().is_file()
    except OSError:
        return False


def build_asset_dependencies(
    scenes: tuple[ExportTimelineScene, ...],
    clip_paths: dict[str, tuple[str, str, int | None]],
) -> tuple[ExportAssetDependency, ...]:
    seen: set[str] = set()
    out: list[ExportAssetDependency] = []
    for sc in scenes:
        cid = sc.selected_clip_id
        if not cid or cid in seen:
            continue
        seen.add(cid)
        path, filename, dur = clip_paths.get(cid, ("", "", None))
        out.append(
            ExportAssetDependency(
                clip_id=cid,
                absolute_path=path,
                exists_on_disk=_path_exists(path),
                duration_ms=dur,
                filename=filename,
            )
        )
    return tuple(out)


def build_export_manifest_entries(
    bundle: ProjectEditorialBundle,
    clip_paths: dict[str, str],
) -> tuple[ExportManifestEntry, ...]:
    entries: list[ExportManifestEntry] = []
    for sc in sorted(bundle.scenes, key=lambda s: s.scene_index):
        cid = sc.selected_clip_id
        path = clip_paths.get(cid, "") if cid else ""
        entries.append(
            ExportManifestEntry(
                scene_id=sc.scene_id,
                scene_index=sc.scene_index,
                start_ms=sc.start_ms,
                end_ms=sc.end_ms,
                clip_id=cid,
                clip_path=path or None,
                clip_ready=bool(cid and _path_exists(path)),
            )
        )
    return tuple(entries)


def build_export_manifest(
    bundle: ProjectEditorialBundle,
    clip_paths: dict[str, str],
) -> ExportManifest:
    entries = build_export_manifest_entries(bundle, clip_paths)
    missing = tuple(
        f"scene_{e.scene_index}_clip_missing"
        for e in entries
        if e.clip_id and not e.clip_ready
    )
    return ExportManifest(
        project_id=bundle.project_id,
        project_name=bundle.project_name,
        timeline_duration_ms=bundle_timeline_duration_ms(bundle.scenes),
        audio_path=bundle.audio_file_path,
        entries=entries,
        missing_assets=missing,
    )


def build_capcut_manifest(
    bundle: ProjectEditorialBundle,
    clip_paths: dict[str, tuple[str, str, int | None]],
) -> CapCutManifest:
    deps = build_asset_dependencies(bundle.scenes, clip_paths)
    path_by_clip = {d.clip_id: d.absolute_path for d in deps}
    exists_by_clip = {d.clip_id: d.exists_on_disk for d in deps}
    warnings: list[str] = []
    entries: list[CapCutTrackEntry] = []
    for order, sc in enumerate(sorted(bundle.scenes, key=lambda s: s.scene_index)):
        cid = sc.selected_clip_id
        clip_path = path_by_clip.get(cid, "") if cid else None
        clip_exists = exists_by_clip.get(cid, False) if cid else False
        if cid and not clip_exists:
            warnings.append(f"scene_{sc.scene_index}_clip_not_on_disk")
        if not cid:
            warnings.append(f"scene_{sc.scene_index}_no_clip_selected")
        entries.append(
            CapCutTrackEntry(
                order=order,
                scene_id=sc.scene_id,
                scene_index=sc.scene_index,
                timeline_start_ms=sc.start_ms,
                timeline_end_ms=sc.end_ms,
                duration_ms=sc.duration_ms,
                clip_id=cid,
                clip_path=clip_path,
                clip_exists=clip_exists,
                text=sc.text,
                concept=sc.concept,
                narrative_function=sc.narrative_function,
            )
        )
    if bundle.audio_file_path and not _path_exists(bundle.audio_file_path):
        warnings.append("audio_master_not_on_disk")
    return CapCutManifest(
        project_id=bundle.project_id,
        project_name=bundle.project_name,
        audio_master_path=bundle.audio_file_path,
        timeline_duration_ms=bundle_timeline_duration_ms(bundle.scenes),
        entries=tuple(entries),
        asset_dependencies=deps,
        warnings=tuple(warnings),
    )
