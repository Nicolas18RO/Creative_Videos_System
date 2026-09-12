import { useCallback, useEffect, useMemo, useRef } from "react";

import { fetchPlaybackSession } from "../api/playbackApi";
import { createPlaybackOrchestrator } from "../state/playbackStore";
import { usePlaybackStore } from "../state/playbackStore";

type Options = {
  onSceneIndex?: (sceneIndex: number) => void;
};

export function usePlaybackStudio(projectId: string | null, options?: Options) {
  const onSceneIndexRef = useRef(options?.onSceneIndex);
  onSceneIndexRef.current = options?.onSceneIndex;

  const orchestratorRef = useRef<ReturnType<typeof createPlaybackOrchestrator> | null>(null);
  if (!orchestratorRef.current) {
    orchestratorRef.current = createPlaybackOrchestrator((idx) => {
      onSceneIndexRef.current?.(idx);
    });
  }
  const orchestrator = orchestratorRef.current;

  const session = usePlaybackStore((s) => s.session);
  const engineState = usePlaybackStore((s) => s.engineState);
  const mode = usePlaybackStore((s) => s.mode);
  const currentTimeSec = usePlaybackStore((s) => s.currentTimeSec);
  const isPlaying = usePlaybackStore((s) => s.isPlaying);
  const loopScene = usePlaybackStore((s) => s.loopScene);
  const activeSceneIndex = usePlaybackStore((s) => s.activeSceneIndex);
  const error = usePlaybackStore((s) => s.error);

  const load = useCallback(async () => {
    if (!projectId) {
      orchestrator.reset();
      return;
    }
    const { patch } = usePlaybackStore.getState();
    orchestrator.setLoading();
    patch({ error: null });
    try {
      const dto = await fetchPlaybackSession(projectId);
      orchestrator.loadSession(dto);
    } catch (e) {
      patch({ error: e instanceof Error ? e.message : String(e) });
      orchestrator.setError();
    }
  }, [orchestrator, projectId]);

  useEffect(() => {
    void load();
    return () => orchestrator.reset();
  }, [load]);

  const snapshot = useMemo(
    () => orchestrator.getSnapshot(),
    [orchestrator, session, engineState, mode, currentTimeSec, isPlaying, loopScene, activeSceneIndex],
  );

  return {
    session,
    engineState,
    error,
    snapshot,
    orchestrator,
    reload: load,
  };
}
