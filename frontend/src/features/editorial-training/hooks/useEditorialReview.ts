import { useCallback } from "react";

import { getTrainingSession } from "../api/editorialTrainingApi";
import {
  bulkReviewAction,
  bulkSceneReviewStatus,
  fetchReviewSummary,
  mergeScenes,
  setSceneReviewStatus,
} from "../api/editorialReviewApi";
import type { EditorialReviewSummaryDto, ReviewStatus } from "../types/trainingWorkspace";
import { useTimelineDraftStore } from "../state/timelineDraftStore";
import { useTrainingWorkspaceStore } from "../state/trainingWorkspaceStore";

export function useEditorialReview() {
  const setLoading = useTrainingWorkspaceStore((s) => s.setLoading);
  const setError = useTrainingWorkspaceStore((s) => s.setError);
  const setReviewSummary = useTrainingWorkspaceStore((s) => s.setReviewSummary);
  const applyReviewStatus = useTrainingWorkspaceStore((s) => s.applyReviewStatus);
  const sessionId = useTrainingWorkspaceStore((s) => s.sessionId);
  const workspace = useTrainingWorkspaceStore((s) => s.workspace);

  const reloadSummary = useCallback(async (): Promise<EditorialReviewSummaryDto | null> => {
    if (!sessionId || !workspace?.session.creative_id) return null;
    setLoading(true);
    setError(null);
    try {
      const summary = await fetchReviewSummary(sessionId, workspace.session.creative_id);
      setReviewSummary(summary);
      for (const st of summary.scene_states) {
        const idx = Number(st.scene_id);
        if (!Number.isNaN(idx)) {
          applyReviewStatus(idx, st.status as ReviewStatus);
        }
      }
      return summary;
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      return null;
    } finally {
      setLoading(false);
    }
  }, [applyReviewStatus, sessionId, setError, setLoading, setReviewSummary, workspace?.session.creative_id]);

  const reviewScene = useCallback(
    async (sceneIndex: number, status: ReviewStatus) => {
      if (!sessionId) return;
      const scene =
        useTimelineDraftStore.getState().draftScenes.find((s) => s.scene_index === sceneIndex) ??
        useTrainingWorkspaceStore.getState().sceneDrafts.find((s) => s.scene_index === sceneIndex);
      setLoading(true);
      setError(null);
      try {
        await setSceneReviewStatus(String(sceneIndex), {
          session_id: sessionId,
          status,
          clip_id: scene?.clip_id,
          narrative_function: scene?.narrative_intent ?? scene?.narrative_role,
          transition_type: scene?.transition_type,
        });
        applyReviewStatus(sceneIndex, status);
        await reloadSummary();
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
      } finally {
        setLoading(false);
      }
    },
    [applyReviewStatus, reloadSummary, sessionId, setError, setLoading],
  );

  const bulkReview = useCallback(
    async (sceneIndices: number[], status: ReviewStatus) => {
      if (!sessionId) return;
      setLoading(true);
      try {
        await bulkSceneReviewStatus({
          session_id: sessionId,
          scene_ids: sceneIndices.map(String),
          status,
        });
        sceneIndices.forEach((i) => applyReviewStatus(i, status));
        await reloadSummary();
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
      } finally {
        setLoading(false);
      }
    },
    [applyReviewStatus, reloadSummary, sessionId, setError, setLoading],
  );

  const runBulkAction = useCallback(
    async (action: string, threshold = 0.75) => {
      if (!sessionId || !workspace?.session.creative_id) return;
      setLoading(true);
      try {
        const summary = await bulkReviewAction(sessionId, {
          session_id: sessionId,
          creative_id: workspace.session.creative_id,
          action,
          confidence_threshold: threshold,
        });
        setReviewSummary(summary);
        for (const st of summary.scene_states) {
          const idx = Number(st.scene_id);
          if (!Number.isNaN(idx)) applyReviewStatus(idx, st.status as ReviewStatus);
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
      } finally {
        setLoading(false);
      }
    },
    [applyReviewStatus, sessionId, setError, setLoading, setReviewSummary, workspace?.session.creative_id],
  );

  const mergeWithNext = useCallback(
    async (sceneIndexA: number, sceneIndexB: number) => {
      if (!sessionId || !workspace?.session.creative_id) return;
      setLoading(true);
      try {
        const summary = await mergeScenes({
          session_id: sessionId,
          creative_id: workspace.session.creative_id,
          scene_index_a: sceneIndexA,
          scene_index_b: sceneIndexB,
        });
        setReviewSummary(summary);
        const w = await getTrainingSession(sessionId);
        const store = useTrainingWorkspaceStore.getState();
        store.hydrateScenesFromWorkspace(w);
        store.setWorkspace(w);
        store.clearSelection();
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
      } finally {
        setLoading(false);
      }
    },
    [sessionId, setError, setLoading, setReviewSummary, workspace?.session.creative_id],
  );

  return { reloadSummary, reviewScene, bulkReview, runBulkAction, mergeWithNext };
}
