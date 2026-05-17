import { useCallback } from "react";

import { fetchMergePreview } from "../api/timelinePrecisionApi";
import { useEditorialReview } from "../hooks/useEditorialReview";
import { useTrainingWorkspaceStore } from "../state/trainingWorkspaceStore";
import { useTimelineDraftStore } from "../state/timelineDraftStore";
import { MergePreviewCard } from "./timeline/MergePreviewCard";
import { TimelineReviewToolbar } from "./TimelineReviewToolbar";
import { TimelineSceneCard } from "./TimelineSceneCard";

function nextMergeTarget(scenes: { scene_index: number; review_status?: string }[], index: number): number | null {
  const sorted = [...scenes]
    .filter((s) => s.review_status !== "merged")
    .sort((a, b) => a.scene_index - b.scene_index);
  const pos = sorted.findIndex((s) => s.scene_index === index);
  if (pos < 0 || pos >= sorted.length - 1) return null;
  return sorted[pos + 1].scene_index;
}

export function TimelineWorkspace() {
  const draftScenes = useTimelineDraftStore((s) => s.draftScenes);
  const patchDraft = useTimelineDraftStore((s) => s.patchDraft);
  const setSceneTiming = useTimelineDraftStore((s) => s.setSceneTiming);
  const resetScene = useTimelineDraftStore((s) => s.resetScene);
  const mergePreview = useTimelineDraftStore((s) => s.mergePreview);
  const mergePair = useTimelineDraftStore((s) => s.mergePair);
  const merging = useTimelineDraftStore((s) => s.merging);
  const setMergePreview = useTimelineDraftStore((s) => s.setMergePreview);
  const setMerging = useTimelineDraftStore((s) => s.setMerging);
  const validation = useTimelineDraftStore((s) => s.validation);

  const loading = useTrainingWorkspaceStore((s) => s.loading);
  const selected = useTrainingWorkspaceStore((s) => s.selectedSceneIndices);
  const toggleSceneSelection = useTrainingWorkspaceStore((s) => s.toggleSceneSelection);
  const workspace = useTrainingWorkspaceStore((s) => s.workspace);
  const sessionId = useTrainingWorkspaceStore((s) => s.sessionId);
  const setError = useTrainingWorkspaceStore((s) => s.setError);
  const initFromScenes = useTimelineDraftStore((s) => s.initFromScenes);

  const { reviewScene, mergeWithNext } = useEditorialReview();

  const timelineDuration = Math.max(...draftScenes.map((s) => s.time_end), 1);

  const issueForScene = useCallback(
    (idx: number) => validation?.issues.find((i) => i.scene_index === idx)?.message ?? null,
    [validation],
  );

  const openMergePreview = useCallback(
    async (a: number, b: number) => {
      const creativeId = workspace?.session.creative_id;
      if (!creativeId) return;
      try {
        const preview = await fetchMergePreview({
          creative_id: creativeId,
          scene_index_a: a,
          scene_index_b: b,
        });
        setMergePreview(preview, { a, b });
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
      }
    },
    [setError, setMergePreview, workspace?.session.creative_id],
  );

  if (!draftScenes.length) {
    return (
      <section className="et-card">
        <h2>Revisión editorial — escenas</h2>
        <p className="et-muted">Cuando el análisis termine, las escenas aparecerán aquí para revisión humana.</p>
      </section>
    );
  }

  const sorted = [...draftScenes].sort((a, b) => a.scene_index - b.scene_index);

  return (
    <section className="et-card">
      <h2>Revisión editorial — escenas</h2>
      <p className="et-muted" style={{ marginBottom: 10 }}>
        Recorte IN/OUT con precisión de milisegundos. Shift+clic para selección múltiple.
      </p>
      <TimelineReviewToolbar disabled={loading} />
      <div className="et-scene-grid" style={{ marginTop: 14 }}>
        {sorted.map((s) => {
          const mergeTarget = nextMergeTarget(draftScenes, s.scene_index);
          return (
            <TimelineSceneCard
              key={`${s.scene_index}-${s.review_status}-${s.time_start}-${s.time_end}`}
              scene={s}
              disabled={loading || merging}
              selected={selected.includes(s.scene_index)}
              timelineDuration={timelineDuration}
              validationMessage={issueForScene(s.scene_index)}
              onSelect={(shift) => toggleSceneSelection(s.scene_index, shift)}
              onPatch={(p) => patchDraft(s.scene_index, p)}
              onTimingChange={(start, end) => setSceneTiming(s.scene_index, start, end)}
              onResetScene={() => resetScene(s.scene_index)}
              onAccept={() => void reviewScene(s.scene_index, "accepted")}
              onReject={() => void reviewScene(s.scene_index, "rejected")}
              onRestore={() => void reviewScene(s.scene_index, "pending")}
              onMergeNext={mergeTarget !== null ? () => void openMergePreview(s.scene_index, mergeTarget) : undefined}
            />
          );
        })}
      </div>

      {mergePreview && mergePair ? (
        <MergePreviewCard
          preview={mergePreview}
          sceneA={draftScenes.find((s) => s.scene_index === mergePair.a)}
          sceneB={draftScenes.find((s) => s.scene_index === mergePair.b)}
          merging={merging}
          onCancel={() => setMergePreview(null, null)}
          onConfirm={() => {
            setMerging(true);
            void mergeWithNext(mergePair.a, mergePair.b)
              .then(async () => {
                if (sessionId) {
                  const { getTrainingSession } = await import("../api/editorialTrainingApi");
                  const w = await getTrainingSession(sessionId);
                  useTrainingWorkspaceStore.getState().hydrateScenesFromWorkspace(w);
                  initFromScenes(useTrainingWorkspaceStore.getState().sceneDrafts);
                }
              })
              .finally(() => {
                setMerging(false);
                setMergePreview(null, null);
              });
          }}
        />
      ) : null}
    </section>
  );
}
