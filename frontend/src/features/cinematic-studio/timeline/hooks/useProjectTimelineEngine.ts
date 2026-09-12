import { useCallback, useEffect, useRef } from "react";

import {
  getProjectTimeline,
  mergeProjectTimelineScenes,
  reorderProjectTimeline,
  replaceProjectTimelineClip,
  splitProjectTimelineScene,
  trimProjectTimelineScene,
} from "../api/projectTimelineApi";
import type { ProjectTimelineSnapshotDto } from "../types/timelineEngine";
import { useTimelineEngineStore } from "../state/timelineEngineStore";

/** Orquestación timeline: mutex de mutación + sync servidor (sin lógica editorial). */
export function useProjectTimelineEngine(projectId: string | null) {
  const hydrate = useTimelineEngineStore((s) => s.hydrate);
  const applyServerSnapshot = useTimelineEngineStore((s) => s.applyServerSnapshot);
  const setSyncing = useTimelineEngineStore((s) => s.setSyncing);
  const setMutationError = useTimelineEngineStore((s) => s.setMutationError);
  const snapshotBeforeMutation = useTimelineEngineStore((s) => s.snapshotBeforeMutation);
  const reset = useTimelineEngineStore((s) => s.reset);
  const mutexRef = useRef(false);

  const runMutation = useCallback(
    async (fn: () => Promise<ProjectTimelineSnapshotDto>) => {
      if (!projectId) return;
      if (mutexRef.current) {
        setMutationError("Espera a que termine la operación anterior.");
        return;
      }
      mutexRef.current = true;
      snapshotBeforeMutation();
      setSyncing(true);
      setMutationError(null);
      try {
        const snap = await fn();
        applyServerSnapshot(snap.scenes, snap.timeline_duration_sec);
      } catch (e) {
        setMutationError(e instanceof Error ? e.message : String(e));
        const reload = await getProjectTimeline(projectId);
        applyServerSnapshot(reload.scenes, reload.timeline_duration_sec);
      } finally {
        setSyncing(false);
        mutexRef.current = false;
      }
    },
    [applyServerSnapshot, projectId, setMutationError, setSyncing, snapshotBeforeMutation],
  );

  const load = useCallback(async () => {
    if (!projectId) {
      reset();
      return;
    }
    setSyncing(true);
    setMutationError(null);
    try {
      const snap = await getProjectTimeline(projectId);
      hydrate(projectId, snap.scenes, snap.timeline_duration_sec);
    } catch (e) {
      setMutationError(e instanceof Error ? e.message : String(e));
    } finally {
      setSyncing(false);
    }
  }, [hydrate, projectId, reset, setMutationError, setSyncing]);

  useEffect(() => {
    void load();
    return () => useTimelineEngineStore.getState().reset();
  }, [load]);

  const reorder = useCallback(
    (fromIndex: number, toIndex: number) =>
      runMutation(() => reorderProjectTimeline(projectId!, fromIndex, toIndex)),
    [projectId, runMutation],
  );

  const merge = useCallback(
    (a: number, b: number) => runMutation(() => mergeProjectTimelineScenes(projectId!, a, b)),
    [projectId, runMutation],
  );

  const split = useCallback(
    (sceneId: string, splitAtMs: number) =>
      runMutation(() => splitProjectTimelineScene(projectId!, sceneId, splitAtMs)),
    [projectId, runMutation],
  );

  const trim = useCallback(
    (sceneId: string, startMs: number, endMs: number) =>
      runMutation(() => trimProjectTimelineScene(projectId!, sceneId, startMs, endMs)),
    [projectId, runMutation],
  );

  const replaceClip = useCallback(
    (sceneId: string, clipId: string) =>
      runMutation(() => replaceProjectTimelineClip(projectId!, sceneId, clipId)),
    [projectId, runMutation],
  );

  return { load, reorder, merge, split, trim, replaceClip };
}
