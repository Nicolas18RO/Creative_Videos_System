import type {
  MergePreviewResultDto,
  TimelineSaveAdjustmentsResponseDto,
  TimelineValidationResultDto,
} from "../types/timelinePrecision";
import type { TimelineScenePayload } from "../types/trainingWorkspace";

const apiBase = () => (import.meta.env.VITE_API_BASE ?? "").replace(/\/$/, "") || "";

async function parseJson<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  return (await res.json()) as T;
}

export async function validateTimelineDraft(body: {
  session_id: string;
  scenes: Array<{ scene_index: number; start_time: number; end_time: number }>;
  timeline_duration?: number | null;
}): Promise<TimelineValidationResultDto> {
  const res = await fetch(`${apiBase()}/editorial-timeline/validate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return parseJson(res);
}

export async function fetchMergePreview(body: {
  creative_id: string;
  scene_index_a: number;
  scene_index_b: number;
}): Promise<MergePreviewResultDto> {
  const res = await fetch(`${apiBase()}/editorial-timeline/merge-preview`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return parseJson(res);
}

export async function saveTimelineAdjustments(
  sessionId: string,
  scenes: TimelineScenePayload[],
  adjustmentReason = "human_trim",
): Promise<TimelineSaveAdjustmentsResponseDto> {
  const res = await fetch(`${apiBase()}/editorial-timeline/sessions/${encodeURIComponent(sessionId)}/save-adjustments`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, scenes, adjustment_reason: adjustmentReason }),
  });
  return parseJson(res);
}
