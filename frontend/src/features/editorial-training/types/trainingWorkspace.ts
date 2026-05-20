/** Contratos alineados con la API FastAPI (presentación). */

export type EditorialTrainingSessionDto = {
  session_id: string;
  creative_id: string;
  project_id: string | null;
  status: string;
  final_video_path: string;
  audio_path: string;
  corrections_count: number;
  created_at: string;
  updated_at: string;
  project_label: string;
  creative_label: string;
  product_category: string;
  notes: string;
};

export type TimelineSceneCardDto = {
  scene_index: number;
  thumbnail_url: string;
  preview_video_url: string;
  hook_score: number;
  scene_type_label: string;
  narrative_role: string;
  narrative_intent?: string;
  clip_source_taxonomy?: string;
  auto_clip_source_taxonomy?: string;
  human_clip_source_taxonomy?: string | null;
  auto_narrative_intent?: string;
  human_narrative_intent?: string | null;
  emotional_intent?: string;
  auto_emotional_intent?: string;
  human_emotional_intent?: string | null;
  audio_fragment_text?: string;
  visual_style_label?: string;
  has_narrative_intent_override?: boolean;
  has_clip_taxonomy_override?: boolean;
  auto_narrative_role?: string;
  human_narrative_role?: string | null;
  has_category_override?: boolean;
  time_start: number;
  time_end: number;
  duration_seconds: number;
  energy_label: string;
  motion_intensity: number;
  visual_energy: number;
  transition_type: string;
  semantic_tags: string[];
  emotion_tags: string[];
  clip_id: string;
  review_status?: string;
  confidence_score?: number;
  merged_into_scene_id?: string | null;
};

export type EditorialTrainingSummaryDto = {
  total_scenes: number;
  hooks_detected: number;
  pacing_score: number;
  average_pacing: number;
  motion_density: number;
  style_visual_dynamism: number;
  corrections_applied: number;
  clip_accept_count: number;
  clip_reject_count: number;
};

export type EditorialTrainingWorkspaceGetDto = {
  session: EditorialTrainingSessionDto;
  timeline: Record<string, unknown> | null;
  scene_cards: TimelineSceneCardDto[];
  summary: EditorialTrainingSummaryDto | null;
  review_summary?: EditorialReviewSummaryDto | null;
};

export type UploadAssetDto = {
  session_id: string;
  path: string;
  stored_filename: string;
  size_bytes: number;
  duration_ms: number | null;
};

export type EditorialTrainingAnalyzeResponseDto = {
  session: EditorialTrainingSessionDto;
  timeline: Record<string, unknown> | null;
  scene_cards: TimelineSceneCardDto[];
  summary: EditorialTrainingSummaryDto | null;
  analysis_warning: string | null;
};

export type TrainingStepId = 1 | 2 | 3 | 4 | 5 | 6 | 7;

export type ReviewStatus = "pending" | "accepted" | "rejected" | "merged" | "edited";

export type EditorialReviewSummaryDto = {
  session_id: string;
  total_scenes: number;
  pending: number;
  accepted: number;
  rejected: number;
  merged: number;
  edited: number;
  scene_states: Array<{
    scene_id: string;
    status: string;
    reviewed_at: string | null;
    reviewer: string;
    correction_reason: string;
    merged_into_scene_id: string | null;
    confidence_override: number | null;
    notes: string;
  }>;
  pending_scene_ids: string[];
  warnings: string[];
};

export type EditableScene = TimelineSceneCardDto & {
  editor_notes: string;
  review_status: ReviewStatus;
  /** @deprecated use review_status */
  editorial_status: "pending" | "accepted" | "rejected";
};

export type TimelineClipPreviewDto = {
  clip_id: string;
  scene_index: number;
  thumbnail_url: string;
  preview_video_url: string;
  start_time: number;
  end_time: number;
  duration: number;
  motion_score: number;
  narrative_role: string;
  visual_cluster_id: string;
  timeline_position: number;
};

export type TimelineVisualTrackDto = {
  creative_id: string;
  timeline_duration: number;
  clip_previews: TimelineClipPreviewDto[];
  pacing_density: number[];
  transition_density: number[];
  motion_curve: number[];
};

export type TimelineVisualizationDto = {
  track: TimelineVisualTrackDto;
  scene_count: number;
};

export type TimelineScenePayload = {
  scene_index: number;
  clip_id: string;
  start_time: number;
  end_time: number;
  transition_type: string;
  narrative_role: string;
  motion_intensity: number;
  visual_energy: number;
  camera_type: string;
  semantic_tags: string[];
  emotion_tags: string[];
};
