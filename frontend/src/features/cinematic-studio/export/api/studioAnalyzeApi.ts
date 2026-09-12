import { apiBase, parseJsonResponse } from "../../../../shared/api/client";
import type { AnalyzeUploadResultDto } from "../types/export";

export type AnalyzeUploadOptions = {
  projectName?: string;
  productCategory?: string;
  targetAudience?: string;
  persist?: boolean;
  includeClipSearch?: boolean;
  enableIntelligence?: boolean;
};

export async function uploadAndAnalyzeAudio(
  file: File,
  options?: AnalyzeUploadOptions,
): Promise<AnalyzeUploadResultDto> {
  const fd = new FormData();
  fd.append("file", file);
  fd.append("project_name", options?.projectName ?? "Proyecto");
  fd.append("product_category", options?.productCategory ?? "salud/bienestar");
  fd.append("target_audience", options?.targetAudience ?? "adultos 35-55");
  fd.append("persist", String(options?.persist !== false));
  fd.append("include_clip_search", String(options?.includeClipSearch !== false));
  fd.append("enable_intelligence", String(options?.enableIntelligence !== false));

  const res = await fetch(`${apiBase()}/analyze/upload`, { method: "POST", body: fd });
  const data = await parseJsonResponse<{
    project_id: string;
    project_name: string;
    total_duration_ms: number;
  }>(res);
  return {
    project_id: data.project_id,
    project_name: data.project_name,
    total_duration_ms: data.total_duration_ms,
  };
}
