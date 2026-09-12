import { create } from "zustand";

import { PlaybackOrchestrator } from "../services/playbackOrchestrator";
import type { PlaybackMode, PlaybackSessionDto, PlaybackStateId } from "../types/playback";

type PlaybackStore = {
  session: PlaybackSessionDto | null;
  engineState: PlaybackStateId;
  mode: PlaybackMode;
  currentTimeSec: number;
  isPlaying: boolean;
  loopScene: boolean;
  activeSceneIndex: number | null;
  error: string | null;
  syncToken: number;
  orchestrator: PlaybackOrchestrator | null;
  bindOrchestrator: (o: PlaybackOrchestrator) => void;
  patch: (p: Partial<Omit<PlaybackStore, "orchestrator" | "bindOrchestrator" | "patch">>) => void;
};

export const usePlaybackStore = create<PlaybackStore>((set) => ({
  session: null,
  engineState: "idle",
  mode: "timeline",
  currentTimeSec: 0,
  isPlaying: false,
  loopScene: false,
  activeSceneIndex: null,
  error: null,
  syncToken: 0,
  orchestrator: null,
  bindOrchestrator: (o) => set({ orchestrator: o }),
  patch: (p) => set(p),
}));

export function createPlaybackOrchestrator(
  onSceneIndex?: (index: number) => void,
): PlaybackOrchestrator {
  const o = new PlaybackOrchestrator(
    () => {
      const s = usePlaybackStore.getState();
      return {
        session: s.session,
        engineState: s.engineState,
        mode: s.mode,
        currentTimeSec: s.currentTimeSec,
        isPlaying: s.isPlaying,
        loopScene: s.loopScene,
        activeSceneIndex: s.activeSceneIndex,
        syncToken: s.syncToken,
      };
    },
    (patch) => usePlaybackStore.getState().patch(patch),
    onSceneIndex,
  );
  usePlaybackStore.getState().bindOrchestrator(o);
  return o;
}
