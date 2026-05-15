import { useCallback, useRef } from "react";

import { analyzeTrainingSession } from "../api/editorialTrainingApi";
import { useTrainingWorkspaceStore } from "../state/trainingWorkspaceStore";
import type { EditorialTrainingAnalyzeResponseDto, EditorialTrainingWorkspaceGetDto } from "../types/trainingWorkspace";

function toWorkspace(res: EditorialTrainingAnalyzeResponseDto): EditorialTrainingWorkspaceGetDto {
  return {
    session: res.session,
    timeline: res.timeline,
    scene_cards: res.scene_cards,
    summary: res.summary,
  };
}

export function useTimelineAnalysis() {
  const timerRef = useRef<number | null>(null);
  const setLoading = useTrainingWorkspaceStore((s) => s.setLoading);
  const setError = useTrainingWorkspaceStore((s) => s.setError);
  const hydrate = useTrainingWorkspaceStore((s) => s.hydrateScenesFromWorkspace);
  const setWorkspace = useTrainingWorkspaceStore((s) => s.setWorkspace);
  const setAnalysisStage = useTrainingWorkspaceStore((s) => s.setAnalysisStage);

  const runAnalysis = useCallback(
    async (sessionId: string) => {
      setLoading(true);
      setError(null);
      setAnalysisStage(0);
      if (timerRef.current) window.clearInterval(timerRef.current);
      timerRef.current = window.setInterval(() => {
        const cur = useTrainingWorkspaceStore.getState().analysisStage;
        useTrainingWorkspaceStore.getState().setAnalysisStage((cur + 1) % 5);
      }, 850);
      try {
        const res = await analyzeTrainingSession(sessionId);
        const w = toWorkspace(res);
        hydrate(w);
        setWorkspace(w);
        return res;
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
        return null;
      } finally {
        if (timerRef.current) window.clearInterval(timerRef.current);
        timerRef.current = null;
        setAnalysisStage(5);
        setLoading(false);
      }
    },
    [hydrate, setAnalysisStage, setError, setLoading, setWorkspace],
  );

  return { runAnalysis };
}
