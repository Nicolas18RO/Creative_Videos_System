import { apiGet } from "../../../shared/api/client";
import type { ProjectDetailDto, ProjectSummaryDto } from "../types/studio";

export async function listProjects(): Promise<ProjectSummaryDto[]> {
  return apiGet<ProjectSummaryDto[]>("/projects");
}

export async function getProject(projectId: string): Promise<ProjectDetailDto> {
  return apiGet<ProjectDetailDto>(`/projects/${encodeURIComponent(projectId)}`);
}
