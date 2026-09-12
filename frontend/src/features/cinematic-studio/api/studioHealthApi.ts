import { apiGet } from "../../../shared/api/client";
import type { AnalyzeHealthDto } from "../types/studio";

export async function getAnalyzeHealth(probeWhisper = false): Promise<AnalyzeHealthDto> {
  const q = probeWhisper ? "?probe_whisper_model=true" : "";
  return apiGet<AnalyzeHealthDto>(`/analyze/health${q}`);
}
