import { useCallback, useState } from "react";

import { uploadAndAnalyzeAudio } from "../api/studioAnalyzeApi";

export function useStudioAnalyzeUpload(onProjectCreated?: (projectId: string) => void) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [progressLabel, setProgressLabel] = useState<string | null>(null);

  const analyzeFile = useCallback(
    async (file: File, projectName: string) => {
      setBusy(true);
      setError(null);
      setProgressLabel("Subiendo y analizando audio…");
      try {
        const result = await uploadAndAnalyzeAudio(file, { projectName, persist: true });
        setProgressLabel(null);
        onProjectCreated?.(result.project_id);
        return result;
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
        setProgressLabel(null);
        return null;
      } finally {
        setBusy(false);
      }
    },
    [onProjectCreated],
  );

  return { busy, error, progressLabel, analyzeFile };
}
