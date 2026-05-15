import { useCallback } from "react";

import { createTrainingSession, getTrainingSession, type CreateTrainingSessionBody } from "../api/editorialTrainingApi";
import { useTrainingWorkspaceStore } from "../state/trainingWorkspaceStore";

export function useTrainingSession() {
  const setLoading = useTrainingWorkspaceStore((s) => s.setLoading);
  const setError = useTrainingWorkspaceStore((s) => s.setError);
  const hydrate = useTrainingWorkspaceStore((s) => s.hydrateScenesFromWorkspace);
  const setWorkspace = useTrainingWorkspaceStore((s) => s.setWorkspace);
  const setSessionId = useTrainingWorkspaceStore((s) => s.setSessionId);

  const refresh = useCallback(
    async (sessionId: string) => {
      setLoading(true);
      setError(null);
      try {
        const w = await getTrainingSession(sessionId);
        hydrate(w);
        setWorkspace(w);
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
      } finally {
        setLoading(false);
      }
    },
    [hydrate, setError, setLoading, setWorkspace],
  );

  const createTraining = useCallback(
    async (body: CreateTrainingSessionBody) => {
      setLoading(true);
      setError(null);
      try {
        const s = await createTrainingSession(body);
        setSessionId(s.session_id);
        await refresh(s.session_id);
        return s;
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
        return null;
      } finally {
        setLoading(false);
      }
    },
    [refresh, setError, setLoading, setSessionId],
  );

  return { createTraining, refresh };
}
