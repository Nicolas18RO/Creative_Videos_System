import { apiGet } from "../../../shared/api/client";
import type { ProjectGapsDto } from "../types/studio";

export async function getProjectGaps(projectId: string): Promise<ProjectGapsDto> {
  return apiGet<ProjectGapsDto>(`/gaps/${encodeURIComponent(projectId)}`);
}
