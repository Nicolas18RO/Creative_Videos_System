import { useCallback } from "react";

import { getProjectGaps } from "../api/studioGapsApi";
import { getProject } from "../api/studioProjectsApi";
import { saveStudioSession } from "../export/services/studioSessionPersistence";
import { useStudioStore } from "../state/studioStore";

/** Orquesta carga de proyecto + gaps (sin lógica de dominio). */
export function useStudioProject() {
  const selectProject = useStudioStore((s) => s.selectProject);
  const setProjectDetail = useStudioStore((s) => s.setProjectDetail);
  const setGaps = useStudioStore((s) => s.setGaps);
  const selectScene = useStudioStore((s) => s.selectScene);
  const setBusy = useStudioStore((s) => s.setBusy);
  const setError = useStudioStore((s) => s.setError);
  const projectDetail = useStudioStore((s) => s.projectDetail);

  const loadProject = useCallback(
    async (projectId: string, preferredSceneId?: string | null) => {
      selectProject(projectId);
      setBusy(true);
      setError(null);
      try {
        const [detail, gaps] = await Promise.all([getProject(projectId), getProjectGaps(projectId)]);
        setProjectDetail(detail);
        setGaps(gaps);
        const pick =
          preferredSceneId && detail.scenes.some((s) => s.scene_id === preferredSceneId)
            ? preferredSceneId
            : (detail.scenes[0]?.scene_id ?? null);
        selectScene(pick);
        saveStudioSession({ projectId, sceneId: pick });
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
      } finally {
        setBusy(false);
      }
    },
    [selectProject, selectScene, setBusy, setError, setGaps, setProjectDetail],
  );

  const refreshProject = useCallback(async () => {
    const pid = useStudioStore.getState().selectedProjectId;
    if (!pid) return;
    const keepScene = useStudioStore.getState().selectedSceneId;
    setBusy(true);
    setError(null);
    try {
      const [detail, gaps] = await Promise.all([getProject(pid), getProjectGaps(pid)]);
      setProjectDetail(detail);
      setGaps(gaps);
      if (keepScene && detail.scenes.some((s) => s.scene_id === keepScene)) {
        selectScene(keepScene);
      } else {
        selectScene(detail.scenes[0]?.scene_id ?? null);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }, [selectScene, setBusy, setError, setGaps, setProjectDetail]);

  return { loadProject, refreshProject, projectDetail };
}
