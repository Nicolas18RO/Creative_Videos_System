export type MergePreviewSceneSliceDto = {
  scene_index: number;
  start_time: number;
  end_time: number;
  duration: number;
  clip_id: string;
  narrative_role: string;
};

export type MergePreviewResultDto = {
  scene_a: MergePreviewSceneSliceDto;
  scene_b: MergePreviewSceneSliceDto;
  merged: MergePreviewSceneSliceDto;
  removed_boundary_time: number;
  total_duration: number;
};

export type TimelineValidationIssueDto = {
  code: string;
  message: string;
  scene_index: number | null;
  related_scene_index: number | null;
};

export type TimelineValidationResultDto = {
  valid: boolean;
  issues: TimelineValidationIssueDto[];
  normalized: Array<{ scene_index: number; start_time: number; end_time: number }>;
};

export type TimelineSaveAdjustmentsResponseDto = {
  validation: TimelineValidationResultDto;
  adjustments_saved: Array<{
    session_id: string;
    scene_index: number;
    auto_detected_start_time: number;
    human_adjusted_start_time: number;
    timing_adjustment_delta: number;
  }>;
  timeline: Record<string, unknown> | null;
};
