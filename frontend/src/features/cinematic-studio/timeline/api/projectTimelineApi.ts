import { apiGet, apiPost } from "../../../../shared/api/client";
import type { ProjectTimelineSnapshotDto } from "../types/timelineEngine";

export async function getProjectTimeline(projectId: string): Promise<ProjectTimelineSnapshotDto> {
  return apiGet<ProjectTimelineSnapshotDto>(`/projects/${encodeURIComponent(projectId)}/timeline`);
}

export async function reorderProjectTimeline(
  projectId: string,
  fromIndex: number,
  toIndex: number,
): Promise<ProjectTimelineSnapshotDto> {
  return apiPost<ProjectTimelineSnapshotDto>(
    `/projects/${encodeURIComponent(projectId)}/timeline/reorder`,
    { from_index: fromIndex, to_index: toIndex },
  );
}

export async function mergeProjectTimelineScenes(
  projectId: string,
  sceneIndexA: number,
  sceneIndexB: number,
): Promise<ProjectTimelineSnapshotDto> {
  return apiPost<ProjectTimelineSnapshotDto>(
    `/projects/${encodeURIComponent(projectId)}/timeline/merge`,
    { scene_index_a: sceneIndexA, scene_index_b: sceneIndexB },
  );
}

export async function splitProjectTimelineScene(
  projectId: string,
  sceneId: string,
  splitAtMs: number,
): Promise<ProjectTimelineSnapshotDto> {
  return apiPost<ProjectTimelineSnapshotDto>(
    `/projects/${encodeURIComponent(projectId)}/timeline/split`,
    { scene_id: sceneId, split_at_ms: splitAtMs },
  );
}

export async function trimProjectTimelineScene(
  projectId: string,
  sceneId: string,
  startMs: number,
  endMs: number,
): Promise<ProjectTimelineSnapshotDto> {
  return apiPost<ProjectTimelineSnapshotDto>(
    `/projects/${encodeURIComponent(projectId)}/timeline/trim`,
    { scene_id: sceneId, start_ms: startMs, end_ms: endMs },
  );
}

export async function replaceProjectTimelineClip(
  projectId: string,
  sceneId: string,
  clipId: string,
): Promise<ProjectTimelineSnapshotDto> {
  return apiPost<ProjectTimelineSnapshotDto>(
    `/projects/${encodeURIComponent(projectId)}/timeline/replace-clip`,
    { scene_id: sceneId, clip_id: clipId },
  );
}
