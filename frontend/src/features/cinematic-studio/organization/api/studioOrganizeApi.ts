import { apiBase, ApiError, parseJsonResponse } from "../../../../shared/api/client";
import type { OrganizeRequestDto, OrganizeResultDto } from "../../types/studio";

export function buildOrganizePreviewRequest(clipId: string): OrganizeRequestDto {
  return { clip_id: clipId, apply: false };
}

export function buildOrganizeApplyRequest(clipId: string): OrganizeRequestDto {
  return { clip_id: clipId, apply: true };
}

export async function postOrganize(body: OrganizeRequestDto): Promise<OrganizeResultDto> {
  const res = await fetch(`${apiBase()}/organize`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (res.status === 409) {
    return (await res.json()) as OrganizeResultDto;
  }
  return parseJsonResponse<OrganizeResultDto>(res);
}

export async function previewOrganize(clipId: string): Promise<OrganizeResultDto> {
  return postOrganize(buildOrganizePreviewRequest(clipId));
}

export async function applyOrganize(clipId: string): Promise<OrganizeResultDto> {
  return postOrganize(buildOrganizeApplyRequest(clipId));
}

export { ApiError };
