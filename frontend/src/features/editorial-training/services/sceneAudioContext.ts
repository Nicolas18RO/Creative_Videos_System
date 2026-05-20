import type { EditableScene } from "../types/trainingWorkspace";
import { formatTimelineTime } from "./timelineTimeFormat";

/** Texto del audio sincronizado con la escena (prioriza transcripción persistida). */
export function sceneAudioContextText(scene: EditableScene): string {
  const fromSemantic = (scene.audio_fragment_text || "").trim();
  if (fromSemantic) return fromSemantic;
  const fromTags = (scene.semantic_tags || []).filter(Boolean).join(" ").trim();
  if (fromTags) return fromTags;
  return "";
}

export function sceneAudioTimeRangeLabel(scene: EditableScene): string {
  return `${formatTimelineTime(scene.time_start)} → ${formatTimelineTime(scene.time_end)}`;
}

export function sceneHasAudioContext(scene: EditableScene): boolean {
  return sceneAudioContextText(scene).length > 0;
}
