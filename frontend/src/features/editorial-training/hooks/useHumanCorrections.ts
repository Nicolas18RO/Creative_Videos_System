import { useCallback } from "react";

import { postTrainingCorrections, type CorrectionItemPayload } from "../api/editorialTrainingApi";
import { useTrainingWorkspaceStore } from "../state/trainingWorkspaceStore";

export function useHumanCorrections() {
  const setLoading = useTrainingWorkspaceStore((s) => s.setLoading);
  const setError = useTrainingWorkspaceStore((s) => s.setError);

  const sendCorrections = useCallback(
    async (sessionId: string, items: CorrectionItemPayload[], reload: (id: string) => Promise<void>) => {
      setLoading(true);
      setError(null);
      try {
        await postTrainingCorrections(sessionId, items);
        await reload(sessionId);
        return true;
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
        return false;
      } finally {
        setLoading(false);
      }
    },
    [setError, setLoading],
  );

  return { sendCorrections };
}
