import type {
  EditorialTrainingAnalyzeResponseDto,
  EditorialTrainingSessionDto,
  EditorialTrainingWorkspaceGetDto,
  UploadAssetDto,
} from "../types/trainingWorkspace";

const apiBase = () => (import.meta.env.VITE_API_BASE ?? "").replace(/\/$/, "") || "";

async function parseJson<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  return (await res.json()) as T;
}

export type CreateTrainingSessionBody = {
  creative_id?: string;
  project_id?: string | null;
  project_name?: string;
  creative_name?: string;
  product_category?: string;
  notes?: string;
  final_video_path?: string;
  audio_path?: string;
};

export async function createTrainingSession(body: CreateTrainingSessionBody): Promise<EditorialTrainingSessionDto> {
  const res = await fetch(`${apiBase()}/editorial-training/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return parseJson<EditorialTrainingSessionDto>(res);
}

export async function getTrainingSession(sessionId: string): Promise<EditorialTrainingWorkspaceGetDto> {
  const res = await fetch(`${apiBase()}/editorial-training/sessions/${encodeURIComponent(sessionId)}`);
  return parseJson<EditorialTrainingWorkspaceGetDto>(res);
}

export async function uploadTrainingVideo(
  sessionId: string,
  file: File,
  onProgress?: (ratio: number) => void,
): Promise<UploadAssetDto> {
  onProgress?.(0.15);
  const fd = new FormData();
  fd.append("session_id", sessionId);
  fd.append("file", file);
  const res = await fetch(`${apiBase()}/editorial-training/upload/video`, {
    method: "POST",
    body: fd,
  });
  onProgress?.(1);
  return parseJson<UploadAssetDto>(res);
}

export async function uploadTrainingAudio(
  sessionId: string,
  file: File,
  onProgress?: (ratio: number) => void,
): Promise<UploadAssetDto> {
  onProgress?.(0.15);
  const fd = new FormData();
  fd.append("session_id", sessionId);
  fd.append("file", file);
  const res = await fetch(`${apiBase()}/editorial-training/upload/audio`, {
    method: "POST",
    body: fd,
  });
  onProgress?.(1);
  return parseJson<UploadAssetDto>(res);
}

export async function analyzeTrainingSession(sessionId: string): Promise<EditorialTrainingAnalyzeResponseDto> {
  const res = await fetch(`${apiBase()}/editorial-training/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId }),
  });
  return parseJson<EditorialTrainingAnalyzeResponseDto>(res);
}

export async function submitTrainingTimeline(
  sessionId: string,
  scenes: unknown[],
): Promise<Record<string, unknown>> {
  const res = await fetch(`${apiBase()}/editorial-training/sessions/${encodeURIComponent(sessionId)}/timeline`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ scenes }),
  });
  return parseJson<Record<string, unknown>>(res);
}

export type CorrectionItemPayload = {
  event_kind: string;
  reward: number;
  clip_id?: string | null;
  replaced_clip_id?: string | null;
  scene_index?: number | null;
  narrative_function?: string | null;
  transition_type?: string | null;
};

export async function postTrainingCorrections(
  sessionId: string,
  items: CorrectionItemPayload[],
): Promise<EditorialTrainingSessionDto> {
  const res = await fetch(
    `${apiBase()}/editorial-training/sessions/${encodeURIComponent(sessionId)}/corrections`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ items }),
    },
  );
  return parseJson<EditorialTrainingSessionDto>(res);
}

export async function commitTrainingSession(sessionId: string): Promise<EditorialTrainingSessionDto> {
  const res = await fetch(`${apiBase()}/editorial-training/sessions/${encodeURIComponent(sessionId)}/commit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  return parseJson<EditorialTrainingSessionDto>(res);
}
