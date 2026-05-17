import type { TimelineVisualizationDto } from "../types/trainingWorkspace";

const apiBase = () => (import.meta.env.VITE_API_BASE ?? "").replace(/\/$/, "") || "";

async function parseJson<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  return (await res.json()) as T;
}

export function mediaSrc(url: string): string {
  if (!url) return "";
  if (url.startsWith("http")) return url;
  return `${apiBase()}${url.startsWith("/") ? url : `/${url}`}`;
}

export async function fetchTimelineVisualization(creativeId: string): Promise<TimelineVisualizationDto> {
  const res = await fetch(`${apiBase()}/timeline-visualization/${encodeURIComponent(creativeId)}`);
  return parseJson<TimelineVisualizationDto>(res);
}

export async function generateTimelinePreviews(
  creativeId: string,
  force = false,
): Promise<TimelineVisualizationDto> {
  const res = await fetch(`${apiBase()}/timeline-visualization/generate-previews`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ creative_id: creativeId, force }),
  });
  return parseJson<TimelineVisualizationDto>(res);
}

export async function rebuildTimelineVisualization(creativeId: string): Promise<TimelineVisualizationDto> {
  const res = await fetch(`${apiBase()}/timeline-visualization/rebuild`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ creative_id: creativeId }),
  });
  return parseJson<TimelineVisualizationDto>(res);
}
