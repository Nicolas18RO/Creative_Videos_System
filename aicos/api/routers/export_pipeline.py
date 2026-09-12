"""Export pipeline — serialización, snapshots y manifests CapCut (Phase 7.4)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from aicos.application.export_pipeline.presentation import (
    bundle_to_out,
    capcut_manifest_to_out,
    export_manifest_to_out,
    snapshot_meta_list,
    snapshot_to_out,
)
from aicos.database.db import session_scope
from aicos.models.schemas import (
    CapCutManifestOut,
    ExportManifestOut,
    PersistSnapshotOut,
    ProjectEditorialBundleOut,
    ProjectSnapshotListOut,
    ProjectSnapshotOut,
    RestoreSnapshotOut,
    WriteManifestOut,
)
from aicos.services.export_pipeline_factory import build_export_pipeline_service

router = APIRouter()


def _svc():
    return build_export_pipeline_service()


@router.get("/projects/{project_id}/bundle", response_model=ProjectEditorialBundleOut)
def get_project_bundle(project_id: str) -> ProjectEditorialBundleOut:
    with session_scope() as session:
        try:
            bundle = _svc().get_live_bundle(session, project_id)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e
    return bundle_to_out(bundle)


@router.get("/projects/{project_id}/manifest", response_model=ExportManifestOut)
def get_export_manifest(project_id: str) -> ExportManifestOut:
    with session_scope() as session:
        try:
            manifest = _svc().build_export_manifest(session, project_id)
        except ValueError as e:
            code = 404 if "not_found" in str(e) else 400
            raise HTTPException(status_code=code, detail=str(e)) from e
    return export_manifest_to_out(manifest)


@router.get("/projects/{project_id}/capcut-manifest", response_model=CapCutManifestOut)
def get_capcut_manifest(project_id: str) -> CapCutManifestOut:
    with session_scope() as session:
        try:
            manifest = _svc().build_capcut_manifest(session, project_id)
        except ValueError as e:
            code = 404 if "not_found" in str(e) else 400
            raise HTTPException(status_code=code, detail=str(e)) from e
    return capcut_manifest_to_out(manifest)


@router.post("/projects/{project_id}/capcut-manifest/write", response_model=WriteManifestOut)
def write_capcut_manifest(project_id: str) -> WriteManifestOut:
    with session_scope() as session:
        try:
            path = _svc().write_capcut_manifest_file(session, project_id)
        except ValueError as e:
            code = 404 if "not_found" in str(e) else 400
            raise HTTPException(status_code=code, detail=str(e)) from e
    return WriteManifestOut(path=path)


@router.post("/projects/{project_id}/export-manifest/write", response_model=WriteManifestOut)
def write_export_manifest(project_id: str) -> WriteManifestOut:
    with session_scope() as session:
        try:
            path = _svc().write_export_manifest_file(session, project_id)
        except ValueError as e:
            code = 404 if "not_found" in str(e) else 400
            raise HTTPException(status_code=code, detail=str(e)) from e
    return WriteManifestOut(path=path)


@router.get("/projects/{project_id}/snapshots", response_model=ProjectSnapshotListOut)
def list_project_snapshots(project_id: str) -> ProjectSnapshotListOut:
    items = _svc().list_snapshots(project_id)
    return ProjectSnapshotListOut(project_id=project_id, snapshots=snapshot_meta_list(items))


@router.post("/projects/{project_id}/snapshots", response_model=PersistSnapshotOut)
def persist_project_snapshot(project_id: str) -> PersistSnapshotOut:
    with session_scope() as session:
        try:
            sid, path = _svc().persist_snapshot(session, project_id)
        except ValueError as e:
            code = 404 if "not_found" in str(e) else 400
            raise HTTPException(status_code=code, detail=str(e)) from e
    return PersistSnapshotOut(snapshot_id=sid, path=path)


@router.get("/projects/{project_id}/snapshots/{snapshot_id}", response_model=ProjectSnapshotOut)
def get_project_snapshot(project_id: str, snapshot_id: str) -> ProjectSnapshotOut:
    try:
        bundle = _svc().load_snapshot(project_id, snapshot_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return snapshot_to_out(bundle)


@router.post("/projects/{project_id}/snapshots/{snapshot_id}/restore", response_model=RestoreSnapshotOut)
def restore_project_snapshot(project_id: str, snapshot_id: str) -> RestoreSnapshotOut:
    with session_scope() as session:
        try:
            count = _svc().restore_snapshot(session, project_id, snapshot_id)
        except ValueError as e:
            code = 404 if "not_found" in str(e) or "mismatch" in str(e) else 400
            raise HTTPException(status_code=code, detail=str(e)) from e
    return RestoreSnapshotOut(scene_count=count)
