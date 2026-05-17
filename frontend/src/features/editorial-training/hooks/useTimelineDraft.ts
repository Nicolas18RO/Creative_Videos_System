import { useCallback } from "react";

import { saveTimelineAdjustments, validateTimelineDraft } from "../api/timelinePrecisionApi";
import { sceneDraftsToTimelinePayload } from "../services/sceneDraftMapper";
import { useTimelineDraftStore } from "../state/timelineDraftStore";
import { useTrainingWorkspaceStore } from "../state/trainingWorkspaceStore";

export function useTimelineDraft() {
  const sessionId = useTrainingWorkspaceStore((s) => s.sessionId);
  const setError = useTrainingWorkspaceStore((s) => s.setError);
  const draftScenes = useTimelineDraftStore((s) => s.draftScenes);
  const setValidation = useTimelineDraftStore((s) => s.setValidation);
  const setSaving = useTimelineDraftStore((s) => s.setSaving);
  const initFromScenes = useTimelineDraftStore((s) => s.initFromScenes);

  const validateDraft = useCallback(async () => {
    if (!sessionId) return null;
    try {
      const result = await validateTimelineDraft({
        session_id: sessionId,
        scenes: draftScenes
          .filter((s) => s.review_status !== "merged")
          .map((s) => ({ scene_index: s.scene_index, start_time: s.time_start, end_time: s.time_end })),
      });
      setValidation(result);
      return result;
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      return null;
    }
  }, [draftScenes, sessionId, setError, setValidation]);

  const saveDraft = useCallback(
    async (reload: (id: string) => Promise<void>) => {
      if (!sessionId) return false;
      const validation = await validateDraft();
      if (validation && !validation.valid) {
        setError("El timeline tiene errores de validación. Corrígelos antes de guardar.");
        return false;
      }
      setSaving(true);
      setError(null);
      try {
        await saveTimelineAdjustments(sessionId, sceneDraftsToTimelinePayload(draftScenes));
        await reload(sessionId);
        initFromScenes(useTrainingWorkspaceStore.getState().sceneDrafts);
        return true;
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
        return false;
      } finally {
        setSaving(false);
      }
    },
    [draftScenes, initFromScenes, sessionId, setError, setSaving, validateDraft],
  );

  return { validateDraft, saveDraft };
}
