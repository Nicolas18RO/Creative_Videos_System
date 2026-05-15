import { useCallback, useState } from "react";

import { uploadTrainingAudio, uploadTrainingVideo } from "../api/editorialTrainingApi";
import { useTrainingWorkspaceStore } from "../state/trainingWorkspaceStore";

export function useCreativeUpload() {
  const [videoProgress, setVideoProgress] = useState(0);
  const [audioProgress, setAudioProgress] = useState(0);
  const setError = useTrainingWorkspaceStore((s) => s.setError);
  const setLoading = useTrainingWorkspaceStore((s) => s.setLoading);
  const setVideoMeta = useTrainingWorkspaceStore((s) => s.setUploadVideoMeta);
  const setAudioMeta = useTrainingWorkspaceStore((s) => s.setUploadAudioMeta);

  const uploadVideo = useCallback(
    async (sessionId: string, file: File, reload: (id: string) => Promise<void>) => {
      setError(null);
      setLoading(true);
      setVideoProgress(0);
      try {
        const r = await uploadTrainingVideo(sessionId, file, setVideoProgress);
        setVideoMeta({
          filename: r.stored_filename,
          size_bytes: r.size_bytes,
          duration_ms: r.duration_ms,
        });
        await reload(sessionId);
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
      } finally {
        setLoading(false);
        setVideoProgress(0);
      }
    },
    [setError, setLoading, setVideoMeta],
  );

  const uploadAudio = useCallback(
    async (sessionId: string, file: File, reload: (id: string) => Promise<void>) => {
      setError(null);
      setLoading(true);
      setAudioProgress(0);
      try {
        const r = await uploadTrainingAudio(sessionId, file, setAudioProgress);
        setAudioMeta({
          filename: r.stored_filename,
          size_bytes: r.size_bytes,
          duration_ms: r.duration_ms,
        });
        await reload(sessionId);
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
      } finally {
        setLoading(false);
        setAudioProgress(0);
      }
    },
    [setError, setLoading, setAudioMeta],
  );

  return { uploadVideo, uploadAudio, videoProgress, audioProgress };
}
