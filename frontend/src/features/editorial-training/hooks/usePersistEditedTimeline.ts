import { useCallback } from "react";

import { submitTrainingTimeline } from "../api/editorialTrainingApi";
import { sceneDraftsToTimelinePayload } from "../services/sceneDraftMapper";
import { useTrainingWorkspaceStore } from "../state/trainingWorkspaceStore";

export function usePersistEditedTimeline() {
  const setLoading = useTrainingWorkspaceStore((s) => s.setLoading);
  const setError = useTrainingWorkspaceStore((s) => s.setError);
  const sceneDrafts = useTrainingWorkspaceStore((s) => s.sceneDrafts);

  const persistScenes = useCallback(
    async (sessionId: string, reload: (id: string) => Promise<void>) => {
      setLoading(true);
      setError(null);
      try {
        const scenes = sceneDraftsToTimelinePayload(sceneDrafts);
        await submitTrainingTimeline(sessionId, scenes);
        await reload(sessionId);
        return true;
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
        return false;
      } finally {
        setLoading(false);
      }
    },
    [sceneDrafts, setError, setLoading],
  );

  return { persistScenes };
}
