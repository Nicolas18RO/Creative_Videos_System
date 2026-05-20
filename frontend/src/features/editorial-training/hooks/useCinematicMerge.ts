import { useCallback } from "react";

import { mergeScenes } from "../api/editorialReviewApi";
import { getTrainingSession } from "../api/editorialTrainingApi";
import { useTimelineDraftStore } from "../state/timelineDraftStore";
import { useTrainingWorkspaceStore } from "../state/trainingWorkspaceStore";

export function useCinematicMerge() {
  const sessionId = useTrainingWorkspaceStore((s) => s.sessionId);
  const creativeId = useTrainingWorkspaceStore((s) => s.workspace?.session.creative_id);
  const setError = useTrainingWorkspaceStore((s) => s.setError);
  const setReviewSummary = useTrainingWorkspaceStore((s) => s.setReviewSummary);
  const setMergeError = useTimelineDraftStore((s) => s.setMergeError);
  const setMerging = useTimelineDraftStore((s) => s.setMerging);
  const setMergePreview = useTimelineDraftStore((s) => s.setMergePreview);
  const initFromScenes = useTimelineDraftStore((s) => s.initFromScenes);

  const executeMerge = useCallback(
    async (sceneIndexA: number, sceneIndexB: number): Promise<boolean> => {
      if (!sessionId || !creativeId) {
        setMergeError("Sesión o creativo no disponible.");
        return false;
      }
      setMerging(true);
      setMergeError(null);
      try {
        const summary = await mergeScenes({
          session_id: sessionId,
          creative_id: creativeId,
          scene_index_a: sceneIndexA,
          scene_index_b: sceneIndexB,
        });
        setReviewSummary(summary);
        const w = await getTrainingSession(sessionId);
        const ws = useTrainingWorkspaceStore.getState();
        ws.hydrateScenesFromWorkspace(w);
        ws.setWorkspace(w);
        ws.clearSelection();
        initFromScenes(ws.sceneDrafts);
        setMergePreview(null, null, null);
        return true;
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        setMergeError(msg);
        setError(msg);
        return false;
      } finally {
        setMerging(false);
      }
    },
    [creativeId, initFromScenes, sessionId, setError, setMergeError, setMergePreview, setMerging, setReviewSummary],
  );

  return { executeMerge };
}
