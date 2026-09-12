import { apiGet } from "../../../shared/api/client";
import type { LibraryClipsResponseDto, LibraryStatsDto } from "../types/studio";

export async function getLibraryStats(): Promise<LibraryStatsDto> {
  return apiGet<LibraryStatsDto>("/library/stats");
}

export async function listLibraryClips(limit: number, offset: number): Promise<LibraryClipsResponseDto> {
  const q = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  return apiGet<LibraryClipsResponseDto>(`/library/clips?${q}`);
}
