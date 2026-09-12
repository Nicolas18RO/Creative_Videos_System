import type { ProjectTimelineSceneDto, TimelineEngineSceneView } from "../types/timelineEngine";

export function mapTimelineSceneDto(dto: ProjectTimelineSceneDto): TimelineEngineSceneView {
  const concept = dto.concept.trim();
  return {
    sceneId: dto.scene_id,
    sceneIndex: dto.scene_index,
    startSec: dto.start_sec,
    endSec: dto.end_sec,
    durationSec: dto.duration_ms / 1000,
    narrativeFunction: dto.narrative_function,
    conceptPreview: concept.length > 40 ? `${concept.slice(0, 40)}…` : concept || "—",
    selectedClipId: dto.selected_clip_id ?? null,
    isHook: dto.is_hook,
  };
}

export function mapTimelineScenes(dtos: ProjectTimelineSceneDto[]): TimelineEngineSceneView[] {
  return dtos.map(mapTimelineSceneDto);
}

export function msFromSec(sec: number): number {
  return Math.round(sec * 1000);
}

export function secFromMs(ms: number): number {
  return ms / 1000;
}
