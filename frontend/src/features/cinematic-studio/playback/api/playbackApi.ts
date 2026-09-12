import { apiBase, apiGet } from "../../../../shared/api/client";
import type { PlaybackSessionDto, PlaybackWaveformDto } from "../types/playback";

export function playbackMediaUrl(relativePath: string): string {
  const base = apiBase();
  if (!relativePath) return "";
  if (relativePath.startsWith("http")) return relativePath;
  return `${base}${relativePath.startsWith("/") ? "" : "/"}${relativePath}`;
}

export async function fetchPlaybackSession(projectId: string): Promise<PlaybackSessionDto> {
  return apiGet<PlaybackSessionDto>(`/playback/projects/${encodeURIComponent(projectId)}/session`);
}

export async function fetchPlaybackWaveform(projectId: string): Promise<PlaybackWaveformDto> {
  return apiGet<PlaybackWaveformDto>(`/playback/projects/${encodeURIComponent(projectId)}/waveform`);
}
