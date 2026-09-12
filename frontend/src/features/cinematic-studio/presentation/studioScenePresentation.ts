import type {
  CandidateSourceMode,
  RecommendationDetailDto,
  RecommendationDto,
  SceneDetailDto,
} from "../types/studio";

/** Vista de escena para UI — anti-corruption layer (sin ranking ni búsqueda). */

export type ClipCandidateView = {
  clipId: string;
  clipPath: string;
  rank: number;
  finalScore: number;
  similarityScore: number;
  accepted: boolean | null;
  thumbnailUrl: string;
  isSelectedOnTimeline: boolean;
};

export type SceneRailItemView = {
  sceneId: string;
  sceneIndex: number;
  narrativeFunction: string;
  conceptPreview: string;
  isHook: boolean;
  hasGap: boolean;
  selectedClipId: string | null;
};

export type SceneDetailView = {
  sceneId: string;
  sceneIndex: number;
  narrativeFunction: string;
  isHook: boolean;
  genderHint: string;
  concept: string;
  text: string;
  selectedClipId: string | null;
};

export function sceneConceptPreview(concept: string, max = 48): string {
  const t = concept.trim();
  if (t.length <= max) return t || "—";
  return `${t.slice(0, max)}…`;
}

export function mapSceneRailItem(
  scene: SceneDetailDto,
  gapSceneIds: ReadonlySet<string>,
): SceneRailItemView {
  return {
    sceneId: scene.scene_id,
    sceneIndex: scene.scene_index,
    narrativeFunction: scene.narrative_function,
    conceptPreview: sceneConceptPreview(scene.concept),
    isHook: scene.is_hook,
    hasGap: gapSceneIds.has(scene.scene_id),
    selectedClipId: scene.selected_clip_id ?? null,
  };
}

export function mapSceneDetail(scene: SceneDetailDto): SceneDetailView {
  return {
    sceneId: scene.scene_id,
    sceneIndex: scene.scene_index,
    narrativeFunction: scene.narrative_function,
    isHook: scene.is_hook,
    genderHint: scene.gender_hint ?? "—",
    concept: scene.concept,
    text: scene.text,
    selectedClipId: scene.selected_clip_id ?? null,
  };
}

function mapPersistedRecommendation(
  rec: RecommendationDetailDto,
  selectedClipId: string | null,
  thumbnailUrlFor: (clipId: string) => string,
): ClipCandidateView {
  return {
    clipId: rec.clip_id,
    clipPath: rec.clip_path,
    rank: rec.rank,
    finalScore: rec.final_score,
    similarityScore: rec.similarity_score,
    accepted: rec.accepted,
    thumbnailUrl: thumbnailUrlFor(rec.clip_id),
    isSelectedOnTimeline: selectedClipId === rec.clip_id,
  };
}

function mapSearchRecommendation(
  rec: RecommendationDto,
  selectedClipId: string | null,
  thumbnailUrlFor: (clipId: string) => string,
): ClipCandidateView {
  return {
    clipId: rec.clip_id,
    clipPath: rec.clip_path,
    rank: rec.rank,
    finalScore: rec.final_score,
    similarityScore: rec.similarity_score,
    accepted: null,
    thumbnailUrl: thumbnailUrlFor(rec.clip_id),
    isSelectedOnTimeline: selectedClipId === rec.clip_id,
  };
}

export function mapCandidatesForScene(
  scene: SceneDetailDto,
  mode: CandidateSourceMode,
  previewResults: RecommendationDto[] | null,
  thumbnailUrlFor: (clipId: string) => string,
): ClipCandidateView[] {
  const selected = scene.selected_clip_id ?? null;
  if (mode === "preview_search" && previewResults) {
    return previewResults.map((r) => mapSearchRecommendation(r, selected, thumbnailUrlFor));
  }
  return scene.recommendations.map((r) => mapPersistedRecommendation(r, selected, thumbnailUrlFor));
}

export function candidateModeLabel(mode: CandidateSourceMode): string {
  switch (mode) {
    case "preview_search":
      return "Vista: búsqueda nueva (no persistida en el proyecto)";
    case "library_explore":
      return "Vista: similares semánticos (exploración de biblioteca)";
    default:
      return "Recomendaciones persistidas del proyecto";
  }
}
