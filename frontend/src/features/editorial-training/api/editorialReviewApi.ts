import type { EditorialReviewSummaryDto } from "../types/trainingWorkspace";

const apiBase = () => (import.meta.env.VITE_API_BASE ?? "").replace(/\/$/, "") || "";

async function parseJson<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  return (await res.json()) as T;
}

export async function setSceneReviewStatus(
  sceneId: string,
  body: {
    session_id: string;
    status: string;
    notes?: string;
    clip_id?: string;
    narrative_function?: string;
    transition_type?: string;
  },
): Promise<void> {
  await fetch(`${apiBase()}/editorial-review/scenes/${encodeURIComponent(sceneId)}/status`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ingest_feedback: true, reviewer: "human", ...body }),
  }).then(parseJson);
}

export async function bulkSceneReviewStatus(body: {
  session_id: string;
  scene_ids: string[];
  status: string;
}): Promise<EditorialReviewSummaryDto> {
  const res = await fetch(`${apiBase()}/editorial-review/scenes/bulk-status`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ingest_feedback: true, reviewer: "human", correction_reason: "bulk", ...body }),
  });
  return parseJson<EditorialReviewSummaryDto>(res);
}

export async function mergeScenes(body: {
  session_id: string;
  creative_id: string;
  scene_index_a: number;
  scene_index_b: number;
}): Promise<EditorialReviewSummaryDto> {
  const res = await fetch(`${apiBase()}/editorial-review/scenes/merge`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return parseJson<EditorialReviewSummaryDto>(res);
}

export async function fetchReviewSummary(sessionId: string, creativeId: string): Promise<EditorialReviewSummaryDto> {
  const res = await fetch(
    `${apiBase()}/editorial-review/sessions/${encodeURIComponent(sessionId)}/summary?creative_id=${encodeURIComponent(creativeId)}`,
  );
  return parseJson<EditorialReviewSummaryDto>(res);
}

export async function bulkReviewAction(
  sessionId: string,
  body: {
    session_id: string;
    creative_id: string;
    action: string;
    confidence_threshold?: number;
  },
): Promise<EditorialReviewSummaryDto> {
  const res = await fetch(`${apiBase()}/editorial-review/sessions/${encodeURIComponent(sessionId)}/bulk-action`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return parseJson<EditorialReviewSummaryDto>(res);
}
