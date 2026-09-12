import { apiBase, apiGet, parseJsonResponse } from "../../../../shared/api/client";
import type {
  CapCutManifestDto,
  ExportManifestDto,
  ProjectEditorialBundleDto,
  ProjectSnapshotMetaDto,
} from "../types/export";

export async function fetchProjectBundle(projectId: string): Promise<ProjectEditorialBundleDto> {
  return apiGet<ProjectEditorialBundleDto>(`/export/projects/${encodeURIComponent(projectId)}/bundle`);
}

export async function fetchExportManifest(projectId: string): Promise<ExportManifestDto> {
  return apiGet<ExportManifestDto>(`/export/projects/${encodeURIComponent(projectId)}/manifest`);
}

export async function fetchCapCutManifest(projectId: string): Promise<CapCutManifestDto> {
  return apiGet<CapCutManifestDto>(`/export/projects/${encodeURIComponent(projectId)}/capcut-manifest`);
}

export async function listProjectSnapshots(projectId: string): Promise<{ snapshots: ProjectSnapshotMetaDto[] }> {
  return apiGet(`/export/projects/${encodeURIComponent(projectId)}/snapshots`);
}

export async function persistProjectSnapshot(projectId: string): Promise<{ snapshot_id: string; path: string }> {
  const res = await fetch(`${apiBase()}/export/projects/${encodeURIComponent(projectId)}/snapshots`, {
    method: "POST",
  });
  return parseJsonResponse(res);
}

export async function restoreProjectSnapshot(
  projectId: string,
  snapshotId: string,
): Promise<{ scene_count: number }> {
  const res = await fetch(
    `${apiBase()}/export/projects/${encodeURIComponent(projectId)}/snapshots/${encodeURIComponent(snapshotId)}/restore`,
    { method: "POST" },
  );
  return parseJsonResponse(res);
}

export async function writeCapCutManifestFile(projectId: string): Promise<{ path: string }> {
  const res = await fetch(
    `${apiBase()}/export/projects/${encodeURIComponent(projectId)}/capcut-manifest/write`,
    { method: "POST" },
  );
  return parseJsonResponse(res);
}

export async function downloadCapCutManifestJson(projectId: string): Promise<void> {
  const manifest = await fetchCapCutManifest(projectId);
  const blob = new Blob([JSON.stringify(manifest, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `capcut-manifest-${projectId}.json`;
  a.click();
  URL.revokeObjectURL(url);
}
