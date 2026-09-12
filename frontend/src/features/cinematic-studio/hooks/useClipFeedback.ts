import { useCallback } from "react";

import { postFeedback } from "../api/studioFeedbackApi";
import { useStudioProject } from "./useStudioProject";

/** Selección de clip en timeline vía `POST /feedback` (paridad PyQt). */
export function useClipFeedback() {
  const { refreshProject } = useStudioProject();

  const submitFeedback = useCallback(
    async (sceneId: string, clipId: string, accepted: boolean, rank: number) => {
      await postFeedback({ scene_id: sceneId, clip_id: clipId, accepted, rank });
      await refreshProject();
    },
    [refreshProject],
  );

  return { submitFeedback };
}
