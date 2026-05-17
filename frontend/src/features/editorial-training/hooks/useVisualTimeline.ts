import { useCallback, useState } from "react";

import { fetchTimelineVisualization, generateTimelinePreviews } from "../api/timelineVisualizationApi";
import type { TimelineVisualizationDto } from "../types/trainingWorkspace";
import { useTrainingWorkspaceStore } from "../state/trainingWorkspaceStore";

export function useVisualTimeline() {
  const [visual, setVisual] = useState<TimelineVisualizationDto | null>(null);
  const setLoading = useTrainingWorkspaceStore((s) => s.setLoading);
  const setError = useTrainingWorkspaceStore((s) => s.setError);

  const load = useCallback(
    async (creativeId: string) => {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchTimelineVisualization(creativeId);
        setVisual(data);
        return data;
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
        return null;
      } finally {
        setLoading(false);
      }
    },
    [setError, setLoading],
  );

  const regenerate = useCallback(
    async (creativeId: string, force = true) => {
      setLoading(true);
      setError(null);
      try {
        const data = await generateTimelinePreviews(creativeId, force);
        setVisual(data);
        return data;
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
        return null;
      } finally {
        setLoading(false);
      }
    },
    [setError, setLoading],
  );

  return { visual, load, regenerate, setVisual };
}
