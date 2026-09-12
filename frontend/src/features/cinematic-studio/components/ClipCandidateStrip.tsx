import { libraryClipThumbnailUrl } from "../../../shared/media/thumbnailUrl";
import {
  candidateModeLabel,
  mapCandidatesForScene,
} from "../presentation/studioScenePresentation";
import type { CandidateSourceMode, RecommendationDto, SceneDetailDto } from "../types/studio";
import { ClipCandidateCard } from "./ClipCandidateCard";

type Props = {
  scene: SceneDetailDto | null;
  mode: CandidateSourceMode;
  previewResults: RecommendationDto[] | null;
  libraryExploreResults: RecommendationDto[] | null;
  busy: boolean;
  onAccept: (sceneId: string, clipId: string, rank: number) => void;
  onReject: (sceneId: string, clipId: string, rank: number) => void;
};

export function ClipCandidateStrip({
  scene,
  mode,
  previewResults,
  libraryExploreResults,
  busy,
  onAccept,
  onReject,
}: Props) {
  if (!scene && mode !== "library_explore") {
    return <p className="cs-muted">Selecciona un proyecto y una escena.</p>;
  }

  const thumb = (clipId: string) => libraryClipThumbnailUrl(clipId);

  let candidates;
  let allowFeedback = false;

  if (mode === "library_explore" && libraryExploreResults) {
    const fakeScene: SceneDetailDto = {
      scene_id: "",
      scene_index: 0,
      text: "",
      concept: "",
      narrative_function: "",
      is_hook: false,
      recommendations: [],
    };
    candidates = mapCandidatesForScene(fakeScene, mode, libraryExploreResults, thumb);
  } else if (scene) {
    candidates = mapCandidatesForScene(scene, mode, previewResults, thumb);
    allowFeedback = mode === "persisted" || mode === "preview_search";
  } else {
    return <p className="cs-muted">Sin candidatos.</p>;
  }

  return (
    <section className="cs-candidate-strip">
      <header className="cs-candidate-strip__head">
        <h2>Candidatos</h2>
        <p className="cs-candidate-strip__hint">{candidateModeLabel(mode)}</p>
      </header>
      <div className="cs-candidate-strip__scroll">
        {candidates.length === 0 ? (
          <p className="cs-muted">No hay recomendaciones para mostrar.</p>
        ) : (
          candidates.map((c) => (
            <ClipCandidateCard
              key={`${c.clipId}-${c.rank}`}
              candidate={c}
              allowFeedback={allowFeedback && Boolean(scene?.scene_id)}
              disabled={busy}
              onAccept={() => scene && onAccept(scene.scene_id, c.clipId, c.rank)}
              onReject={() => scene && onReject(scene.scene_id, c.clipId, c.rank)}
            />
          ))
        )}
      </div>
    </section>
  );
}
