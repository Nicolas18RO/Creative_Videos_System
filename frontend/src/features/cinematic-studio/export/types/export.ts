/** DTOs del pipeline de exportación (Phase 7.4). */

export type ExportTimelineSceneDto = {
  scene_id: string;
  scene_index: number;
  start_ms: number;
  end_ms: number;
  duration_ms: number;
  text: string;
  concept: string;
  narrative_function: string;
  selected_clip_id?: string | null;
  is_hook: boolean;
};

export type ProjectEditorialBundleDto = {
  format_version: string;
  project_id: string;
  project_name: string;
  status: string;
  audio_file_path?: string | null;
  transcript_path?: string | null;
  scenes: ExportTimelineSceneDto[];
  assets: {
    clip_id: string;
    absolute_path: string;
    exists_on_disk: boolean;
    duration_ms?: number | null;
    filename: string;
  }[];
};

export type CapCutManifestDto = {
  format_version: string;
  project_id: string;
  project_name: string;
  audio_master_path?: string | null;
  timeline_duration_ms: number;
  generated_at?: string | null;
  warnings: string[];
  entries: {
    order: number;
    scene_index: number;
    timeline_start_ms: number;
    timeline_end_ms: number;
    clip_id?: string | null;
    clip_path?: string | null;
    clip_exists: boolean;
    text: string;
  }[];
};

export type ExportManifestDto = {
  format_version: string;
  project_id: string;
  project_name: string;
  timeline_duration_ms: number;
  missing_assets: string[];
  entries: {
    scene_index: number;
    start_ms: number;
    end_ms: number;
    clip_ready: boolean;
  }[];
};

export type ProjectSnapshotMetaDto = {
  snapshot_id: string;
  created_at: string;
  path: string;
};

export type AnalyzeUploadResultDto = {
  project_id: string;
  project_name: string;
  total_duration_ms: number;
};
