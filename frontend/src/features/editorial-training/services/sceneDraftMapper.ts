import type { EditableScene, TimelineScenePayload } from "../types/trainingWorkspace";

const NARRATIVE_OPTIONS = [
  "HOOK",
  "PROBLEM",
  "BENEFIT",
  "RESULT",
  "AUTHORITY",
  "SOCIAL_PROOF",
  "PRODUCT",
  "NATURAL",
  "CTA",
] as const;

export function sceneTypeLabelFromRole(narrativeRole: string): string {
  const nr = (narrativeRole || "").trim().toUpperCase();
  if (nr === "HOOK") return "Hook Scene";
  if (nr === "CTA") return "Call To Action";
  if (nr === "PRODUCT") return "Product Scene";
  if (nr) return nr.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
  return "Scene";
}

export function narrativeRoles(): readonly string[] {
  return NARRATIVE_OPTIONS;
}

export function clipSourceTaxonomies(): readonly string[] {
  return NARRATIVE_OPTIONS;
}

export function narrativeIntents(): readonly string[] {
  return NARRATIVE_OPTIONS;
}

const EMOTIONAL_OPTIONS = ["FEAR", "HOPE", "URGENCY", "TRUST", "CURIOSITY", "EMPATHY", "NEUTRAL"] as const;

export function emotionalIntents(): readonly string[] {
  return EMOTIONAL_OPTIONS;
}

export function energyToVisualEnergy(label: string): number {
  const v = label.toLowerCase();
  if (v === "high") return 0.85;
  if (v === "medium") return 0.5;
  return 0.22;
}

export function visualEnergyToLabel(v: number): string {
  if (v >= 0.66) return "high";
  if (v >= 0.33) return "medium";
  return "low";
}

export function sceneDraftsToTimelinePayload(scenes: EditableScene[]): TimelineScenePayload[] {
  return [...scenes]
    .sort((a, b) => a.scene_index - b.scene_index)
    .map((s) => ({
      scene_index: s.scene_index,
      clip_id: s.clip_id,
      start_time: s.time_start,
      end_time: s.time_end,
      transition_type: s.transition_type || "cut",
      narrative_role: s.narrative_role,
      motion_intensity: s.motion_intensity,
      visual_energy: s.visual_energy,
      camera_type: "",
      semantic_tags: [...s.semantic_tags],
      emotion_tags: [...s.emotion_tags],
    }));
}
