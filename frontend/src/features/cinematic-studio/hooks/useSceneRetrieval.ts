import { useCallback } from "react";

import { postSearch } from "../api/studioSearchApi";
import { useStudioStore } from "../state/studioStore";

/** Re-búsqueda de candidatos para la escena activa (`POST /search`). */
export function useSceneRetrieval() {
  const setPreviewSearchResults = useStudioStore((s) => s.setPreviewSearchResults);
  const clearPreviewSearch = useStudioStore((s) => s.clearPreviewSearch);
  const setBusy = useStudioStore((s) => s.setBusy);
  const setError = useStudioStore((s) => s.setError);

  const researchScene = useCallback(async () => {
    const { projectDetail, selectedSceneId } = useStudioStore.getState();
    if (!projectDetail || !selectedSceneId) return;
    const scene = projectDetail.scenes.find((s) => s.scene_id === selectedSceneId);
    if (!scene) return;

    setBusy(true);
    setError(null);
    try {
      const resp = await postSearch({
        query: (scene.concept || scene.text).slice(0, 200),
        narrative_function: scene.narrative_function,
        gender_hint: scene.gender_hint ?? undefined,
        is_hook: scene.is_hook,
        n_results: 8,
        candidate_pool_size: 24,
      });
      setPreviewSearchResults(resp.results);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }, [setBusy, setError, setPreviewSearchResults]);

  return { researchScene, clearPreviewSearch };
}
