export type EditorialRegistrySessionDto = {
  session_id: string;
  creative_id: string;
  creative_label: string;
  project_label: string;
  product_category: string;
  status: string;
  committed_at: string | null;
  created_at: string;
  updated_at: string;
  scene_count: number;
  duration_seconds: number;
  has_feedback: boolean;
  has_timeline: boolean;
  notes: string;
  corrections_count: number;
};

export type EditorialRegistrySummaryDto = {
  total: number;
  committed: number;
  awaiting_human: number;
  analyzing: number;
  failed: number;
  draft: number;
  ready: number;
  with_timeline: number;
  with_feedback: number;
};

export type EditorialRegistryListDto = {
  sessions: EditorialRegistrySessionDto[];
  summary: EditorialRegistrySummaryDto;
};

export type RegistryStatusFilter = "all" | "committed" | "awaiting_human" | "analyzing" | "failed" | "draft" | "ready";
