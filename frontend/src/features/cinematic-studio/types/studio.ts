/** DTOs alineados con FastAPI — sin lógica de negocio. */

export type ProjectSummaryDto = {
  id: string;
  name: string;
  status: string;
  audio_file_path?: string | null;
  created_at?: string | null;
};

export type RecommendationDetailDto = {
  id: string;
  clip_id: string;
  clip_path: string;
  rank: number;
  similarity_score: number;
  final_score: number;
  accepted: boolean | null;
  thumbnail_path?: string | null;
};

export type SceneDetailDto = {
  scene_id: string;
  scene_index: number;
  text: string;
  concept: string;
  narrative_function: string;
  is_hook: boolean;
  gender_hint?: string | null;
  selected_clip_id?: string | null;
  recommendations: RecommendationDetailDto[];
};

export type ProjectDetailDto = {
  project: ProjectSummaryDto;
  scenes: SceneDetailDto[];
};

export type GapDto = {
  scene_id: string;
  concept: string;
  narrative_function: string;
  gap_type: "tiktok_search" | "ai_generation" | "both";
  tiktok_keywords: string[];
  ai_image_prompt?: string | null;
  ai_motion_prompt?: string | null;
  taxonomy_suggestion?: string;
};

export type GapListItemDto = {
  scene_index: number;
  gap: GapDto;
};

export type ProjectGapsDto = {
  project_id: string;
  project_name?: string | null;
  gaps: GapListItemDto[];
};

export type SearchRequestDto = {
  query: string;
  narrative_function?: string | null;
  gender_hint?: string | null;
  is_hook?: boolean;
  used_clip_ids?: string[];
  n_results?: number;
  candidate_pool_size?: number;
  record_usage?: boolean;
  apply_intelligence?: boolean;
};

export type RecommendationDto = {
  clip_id: string;
  clip_path: string;
  rank: number;
  similarity_score: number;
  taxonomy_boost: number;
  intelligence_boost?: number;
  editorial_learning_boost?: number;
  final_score: number;
  narrative_function?: string | null;
  gender?: string | null;
  thumbnail_path?: string | null;
};

export type SearchResponseDto = {
  results: RecommendationDto[];
  is_gap: boolean;
  query_fingerprint?: string | null;
};

export type FeedbackRequestDto = {
  scene_id: string;
  clip_id: string;
  accepted: boolean;
  rank?: number | null;
};

export type FeedbackResponseDto = {
  updated: number;
  scene_id: string;
  clip_id: string;
};

export type ClipSummaryDto = {
  clip_id: string;
  name: string;
  relative_path?: string;
  file_hash?: string | null;
  scene_id?: string | null;
  duration_ms?: number | null;
  tags?: string | null;
  narrative_function?: string | null;
  subcategory?: string | null;
  semantic_excerpt?: string | null;
};

export type LibraryClipsResponseDto = {
  total: number;
  limit: number;
  offset: number;
  items: ClipSummaryDto[];
};

export type LibraryStatsDto = {
  total_clips: number;
  naming_compliant: number;
};

export type AnalyzeHealthCheckDto = {
  name: string;
  status: "ok" | "warn" | "error";
  message: string;
};

export type AnalyzeHealthDto = {
  ok: boolean;
  overall_status: "healthy" | "unhealthy";
  summary: string;
  checks: AnalyzeHealthCheckDto[];
  timestamp: string;
};

/** Modo de candidatos en UI (espejo PyQt `_search_preview`). */
export type CandidateSourceMode = "persisted" | "preview_search" | "library_explore";
