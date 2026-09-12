import { useCallback, useEffect, useRef } from "react";

import { getAnalyzeHealth } from "../api/studioHealthApi";
import { getLibraryStats, listLibraryClips } from "../api/studioLibraryApi";
import { listProjects } from "../api/studioProjectsApi";
import { loadStudioSession } from "../export/services/studioSessionPersistence";
import { useStudioStore } from "../state/studioStore";

type BootstrapOptions = {
  onRestoreProject?: (projectId: string, sceneId: string | null) => void;
};

/** Carga inicial: salud API, stats biblioteca, primera página clips, proyectos. */
export function useStudioBootstrap(options?: BootstrapOptions) {
  const onRestoreRef = useRef(options?.onRestoreProject);
  onRestoreRef.current = options?.onRestoreProject;
  const sessionRestoreDoneRef = useRef(false);

  const libraryPageSize = useStudioStore((s) => s.libraryPageSize);

  const fetchBootstrap = useCallback(async () => {
    const store = useStudioStore.getState();
    store.setBusy(true);
    store.setError(null);
    try {
      const [health, stats, clips, projects] = await Promise.all([
        getAnalyzeHealth(false),
        getLibraryStats(),
        listLibraryClips(libraryPageSize, 0),
        listProjects(),
      ]);
      store.setHealthOk(health.ok);
      store.setLibraryStats(stats);
      store.resetLibraryList();
      store.setLibraryPage(clips.items, clips.total, clips.offset + clips.items.length);
      store.setProjects(projects);
      return { projects, saved: loadStudioSession() };
    } catch (e) {
      store.setError(e instanceof Error ? e.message : String(e));
      store.setHealthOk(false);
      return null;
    } finally {
      store.setBusy(false);
    }
  }, [libraryPageSize]);

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      const result = await fetchBootstrap();
      if (cancelled || !result) return;
      const { projects, saved } = result;
      if (
        !sessionRestoreDoneRef.current &&
        saved?.projectId &&
        projects.some((p) => p.id === saved.projectId)
      ) {
        sessionRestoreDoneRef.current = true;
        onRestoreRef.current?.(saved.projectId, saved.sceneId);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [fetchBootstrap]);

  const reload = useCallback(async () => {
    await fetchBootstrap();
  }, [fetchBootstrap]);

  return { reload };
}
