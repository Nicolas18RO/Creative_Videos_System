import { create } from "zustand";

import { scenesEqual, applyRedo, applyUndo, pushHistory } from "../services/timelineDraftHistory";
import { roundSeconds } from "../services/timelineTimeFormat";
import type { MergePreviewResultDto, TimelineValidationResultDto } from "../types/timelinePrecision";
import type { EditableScene } from "../types/trainingWorkspace";

type TimelineDraftState = {
  originalScenes: EditableScene[];
  draftScenes: EditableScene[];
  history: EditableScene[][];
  future: EditableScene[][];
  validation: TimelineValidationResultDto | null;
  mergePreview: MergePreviewResultDto | null;
  mergePair: { a: number; b: number } | null;
  merging: boolean;
  saving: boolean;
  initFromScenes: (scenes: EditableScene[]) => void;
  patchDraft: (sceneIndex: number, patch: Partial<EditableScene>) => void;
  setSceneTiming: (sceneIndex: number, timeStart: number, timeEnd: number) => void;
  undo: () => void;
  redo: () => void;
  resetScene: (sceneIndex: number) => void;
  resetTimeline: () => void;
  setValidation: (v: TimelineValidationResultDto | null) => void;
  setMergePreview: (preview: MergePreviewResultDto | null, pair: { a: number; b: number } | null) => void;
  setMerging: (v: boolean) => void;
  setSaving: (v: boolean) => void;
  hasPendingChanges: () => boolean;
  canUndo: () => boolean;
  canRedo: () => boolean;
};

function withHistory(state: TimelineDraftState, nextScenes: EditableScene[]): Partial<TimelineDraftState> {
  return {
    history: pushHistory(state.history, state.draftScenes),
    future: [],
    draftScenes: nextScenes,
  };
}

export const useTimelineDraftStore = create<TimelineDraftState>((set, get) => ({
  originalScenes: [],
  draftScenes: [],
  history: [],
  future: [],
  validation: null,
  mergePreview: null,
  mergePair: null,
  merging: false,
  saving: false,

  initFromScenes: (scenes) =>
    set({
      originalScenes: scenes.map((s) => ({ ...s })),
      draftScenes: scenes.map((s) => ({ ...s })),
      history: [],
      future: [],
      validation: null,
      mergePreview: null,
      mergePair: null,
    }),

  patchDraft: (sceneIndex, patch) =>
    set((state) => {
      const draftScenes = state.draftScenes.map((s) => {
        if (s.scene_index !== sceneIndex) return s;
        const next = { ...s, ...patch };
        if (patch.time_start !== undefined || patch.time_end !== undefined) {
          next.duration_seconds = roundSeconds(next.time_end - next.time_start);
        }
        if (next.review_status === "pending") next.review_status = "edited";
        return next;
      });
      return withHistory(state, draftScenes);
    }),

  setSceneTiming: (sceneIndex, timeStart, timeEnd) => {
    const start = roundSeconds(timeStart);
    const end = roundSeconds(Math.max(start + 0.001, timeEnd));
    get().patchDraft(sceneIndex, {
      time_start: start,
      time_end: end,
      duration_seconds: roundSeconds(end - start),
      review_status: "edited",
    });
  },

  undo: () => {
    const state = get();
    const result = applyUndo(state.history, state.future, state.draftScenes);
    if (!result) return;
    set({ history: result.history, future: result.future, draftScenes: result.current });
  },

  redo: () => {
    const state = get();
    const result = applyRedo(state.history, state.future, state.draftScenes);
    if (!result) return;
    set({ history: result.history, future: result.future, draftScenes: result.current });
  },

  resetScene: (sceneIndex) =>
    set((state) => {
      const orig = state.originalScenes.find((s) => s.scene_index === sceneIndex);
      if (!orig) return state;
      const draftScenes = state.draftScenes.map((s) => (s.scene_index === sceneIndex ? { ...orig } : s));
      return withHistory(state, draftScenes);
    }),

  resetTimeline: () =>
    set((state) => ({
      ...withHistory(state, state.originalScenes.map((s) => ({ ...s }))),
    })),

  setValidation: (validation) => set({ validation }),
  setMergePreview: (mergePreview, mergePair) => set({ mergePreview, mergePair }),
  setMerging: (merging) => set({ merging }),
  setSaving: (saving) => set({ saving }),

  hasPendingChanges: () => {
    const { originalScenes, draftScenes } = get();
    return !scenesEqual(originalScenes, draftScenes);
  },

  canUndo: () => get().history.length > 0,
  canRedo: () => get().future.length > 0,
}));
