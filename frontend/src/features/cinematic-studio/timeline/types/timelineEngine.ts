/** DTOs Phase 7.2 — timeline engine de proyecto. */

export type ProjectTimelineSceneDto = {
  scene_id: string;
  scene_index: number;
  start_ms: number;
  end_ms: number;
  duration_ms: number;
  start_sec: number;
  end_sec: number;
  text: string;
  concept: string;
  narrative_function: string;
  is_hook: boolean;
  gender_hint?: string | null;
  selected_clip_id?: string | null;
};

export type ProjectTimelineSnapshotDto = {
  project_id: string;
  timeline_duration_ms: number;
  timeline_duration_sec: number;
  scenes: ProjectTimelineSceneDto[];
};

export type TimelineEngineSceneView = {
  sceneId: string;
  sceneIndex: number;
  startSec: number;
  endSec: number;
  durationSec: number;
  narrativeFunction: string;
  conceptPreview: string;
  selectedClipId: string | null;
  isHook: boolean;
};
