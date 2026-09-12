import { create } from "zustand";

import { pushTimelineHistory, timelineRedo, timelineUndo } from "../services/timelineEngineHistory";
import type { ProjectTimelineSceneDto } from "../types/timelineEngine";

type TimelineEngineStore = {
  projectId: string | null;
  serverScenes: ProjectTimelineSceneDto[];
  draftScenes: ProjectTimelineSceneDto[];
  history: ProjectTimelineSceneDto[][];
  future: ProjectTimelineSceneDto[][];
  timelineDurationSec: number;
  selectedSceneIndex: number | null;
  mergePair: { a: number; b: number } | null;
  syncing: boolean;
  mutationError: string | null;
  version: number;
  hydrate: (projectId: string, scenes: ProjectTimelineSceneDto[], durationSec: number) => void;
  applyServerSnapshot: (scenes: ProjectTimelineSceneDto[], durationSec: number) => void;
  selectScene: (index: number | null) => void;
  setMergePair: (pair: { a: number; b: number } | null) => void;
  setSyncing: (v: boolean) => void;
  setMutationError: (msg: string | null) => void;
  snapshotBeforeMutation: () => void;
  undoLocal: () => void;
  redoLocal: () => void;
  reset: () => void;
  hasPendingChanges: () => boolean;
};

export const useTimelineEngineStore = create<TimelineEngineStore>((set, get) => ({
  projectId: null,
  serverScenes: [],
  draftScenes: [],
  history: [],
  future: [],
  timelineDurationSec: 1,
  selectedSceneIndex: null,
  mergePair: null,
  syncing: false,
  mutationError: null,
  version: 0,

  hydrate: (projectId, scenes, durationSec) =>
    set({
      projectId,
      serverScenes: scenes.map((s) => ({ ...s })),
      draftScenes: scenes.map((s) => ({ ...s })),
      history: [],
      future: [],
      timelineDurationSec: Math.max(0.001, durationSec),
      selectedSceneIndex: scenes[0]?.scene_index ?? null,
      mergePair: null,
      mutationError: null,
      version: get().version + 1,
    }),

  applyServerSnapshot: (scenes, durationSec) =>
    set((s) => ({
      serverScenes: scenes.map((x) => ({ ...x })),
      draftScenes: scenes.map((x) => ({ ...x })),
      history: [],
      future: [],
      timelineDurationSec: Math.max(0.001, durationSec),
      syncing: false,
      version: s.version + 1,
    })),

  selectScene: (selectedSceneIndex) => set({ selectedSceneIndex, mergePair: null }),

  setMergePair: (mergePair) => set({ mergePair }),

  setSyncing: (syncing) => set({ syncing }),

  setMutationError: (mutationError) => set({ mutationError }),

  snapshotBeforeMutation: () =>
    set((s) => ({
      history: pushTimelineHistory(s.history, s.draftScenes),
      future: [],
    })),

  undoLocal: () => {
    const s = get();
    const r = timelineUndo(s.history, s.future, s.draftScenes);
    if (!r) return;
    set({ history: r.history, future: r.future, draftScenes: r.current });
  },

  redoLocal: () => {
    const s = get();
    const r = timelineRedo(s.history, s.future, s.draftScenes);
    if (!r) return;
    set({ history: r.history, future: r.future, draftScenes: r.current });
  },

  reset: () =>
    set({
      projectId: null,
      serverScenes: [],
      draftScenes: [],
      history: [],
      future: [],
      timelineDurationSec: 1,
      selectedSceneIndex: null,
      mergePair: null,
      syncing: false,
      mutationError: null,
    }),

  hasPendingChanges: () => {
    const { serverScenes, draftScenes } = get();
    if (serverScenes.length !== draftScenes.length) return true;
    return serverScenes.some(
      (s, i) =>
        s.scene_id !== draftScenes[i]?.scene_id ||
        s.start_ms !== draftScenes[i]?.start_ms ||
        s.end_ms !== draftScenes[i]?.end_ms ||
        s.selected_clip_id !== draftScenes[i]?.selected_clip_id,
    );
  },
}));
