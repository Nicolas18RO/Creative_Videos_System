import { create } from "zustand";

import type {
  EditableScene,
  EditorialReviewSummaryDto,
  EditorialTrainingWorkspaceGetDto,
  ReviewStatus,
  TrainingStepId,
} from "../types/trainingWorkspace";

type TrainingWorkspaceState = {
  step: TrainingStepId;
  sessionId: string | null;
  workspace: EditorialTrainingWorkspaceGetDto | null;
  sceneDrafts: EditableScene[];
  reviewSummary: EditorialReviewSummaryDto | null;
  selectedSceneIndices: number[];
  lastSelectedIndex: number | null;
  mergePreview: { a: number; b: number } | null;
  loading: boolean;
  error: string | null;
  analysisStage: number;
  uploadVideoMeta: UploadSlotMeta | null;
  uploadAudioMeta: UploadSlotMeta | null;
  setStep: (step: TrainingStepId) => void;
  setSessionId: (id: string | null) => void;
  setLoading: (v: boolean) => void;
  setError: (msg: string | null) => void;
  setWorkspace: (w: EditorialTrainingWorkspaceGetDto | null) => void;
  hydrateScenesFromWorkspace: (w: EditorialTrainingWorkspaceGetDto) => void;
  patchScene: (sceneIndex: number, patch: Partial<EditableScene>) => void;
  setSceneDrafts: (scenes: EditableScene[]) => void;
  applyReviewStatus: (sceneIndex: number, status: ReviewStatus) => void;
  setReviewSummary: (s: EditorialReviewSummaryDto | null) => void;
  toggleSceneSelection: (sceneIndex: number, shift: boolean) => void;
  clearSelection: () => void;
  setMergePreview: (p: { a: number; b: number } | null) => void;
  setAnalysisStage: (n: number) => void;
  setUploadVideoMeta: (m: UploadSlotMeta | null) => void;
  setUploadAudioMeta: (m: UploadSlotMeta | null) => void;
  reset: () => void;
};

export type UploadSlotMeta = {
  filename: string;
  size_bytes: number;
  duration_ms: number | null;
};

const initial: Pick<
  TrainingWorkspaceState,
  | "step"
  | "sessionId"
  | "workspace"
  | "sceneDrafts"
  | "reviewSummary"
  | "selectedSceneIndices"
  | "lastSelectedIndex"
  | "mergePreview"
  | "loading"
  | "error"
  | "analysisStage"
  | "uploadVideoMeta"
  | "uploadAudioMeta"
> = {
  step: 1,
  sessionId: null,
  workspace: null,
  sceneDrafts: [],
  reviewSummary: null,
  selectedSceneIndices: [],
  lastSelectedIndex: null,
  mergePreview: null,
  loading: false,
  error: null,
  analysisStage: 0,
  uploadVideoMeta: null,
  uploadAudioMeta: null,
};

function cardsToDrafts(w: EditorialTrainingWorkspaceGetDto): EditableScene[] {
  return (w.scene_cards ?? []).map((c) => ({
    ...c,
    editor_notes: "",
    review_status: (c.review_status || "pending") as ReviewStatus,
    editorial_status: mapReviewToLegacy(c.review_status || "pending"),
  }));
}

function mapReviewToLegacy(status: string): "pending" | "accepted" | "rejected" {
  if (status === "accepted") return "accepted";
  if (status === "rejected") return "rejected";
  return "pending";
}

export const useTrainingWorkspaceStore = create<TrainingWorkspaceState>((set, get) => ({
  ...initial,
  setStep: (step) => set({ step }),
  setSessionId: (sessionId) => set({ sessionId }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  setWorkspace: (workspace) => set({ workspace }),
  hydrateScenesFromWorkspace: (w) =>
    set({
      workspace: w,
      sceneDrafts: cardsToDrafts(w),
      reviewSummary: w.review_summary ?? null,
    }),
  patchScene: (sceneIndex, patch) =>
    set((state) => ({
      sceneDrafts: state.sceneDrafts.map((s) => {
        if (s.scene_index !== sceneIndex) return s;
        const next = { ...s, ...patch };
        if (patch.review_status) {
          next.editorial_status = mapReviewToLegacy(patch.review_status);
        }
        if (Object.keys(patch).some((k) => k !== "review_status" && k !== "editor_notes" && k !== "editorial_status")) {
          if (next.review_status === "pending") {
            next.review_status = "edited";
            next.editorial_status = "pending";
          }
        }
        return next;
      }),
    })),
  setSceneDrafts: (sceneDrafts) => set({ sceneDrafts }),
  applyReviewStatus: (sceneIndex, status) =>
    set((state) => ({
      sceneDrafts: state.sceneDrafts.map((s) =>
        s.scene_index === sceneIndex
          ? { ...s, review_status: status, editorial_status: mapReviewToLegacy(status) }
          : s,
      ),
    })),
  setReviewSummary: (reviewSummary) => set({ reviewSummary }),
  toggleSceneSelection: (sceneIndex, shift) => {
    const { selectedSceneIndices, lastSelectedIndex, sceneDrafts } = get();
    if (shift && lastSelectedIndex !== null) {
      const indices = sceneDrafts.map((s) => s.scene_index).sort((a, b) => a - b);
      const a = indices.indexOf(lastSelectedIndex);
      const b = indices.indexOf(sceneIndex);
      if (a >= 0 && b >= 0) {
        const [lo, hi] = a < b ? [a, b] : [b, a];
        const range = indices.slice(lo, hi + 1);
        set({ selectedSceneIndices: Array.from(new Set(range)), lastSelectedIndex: sceneIndex });
        return;
      }
    }
    const exists = selectedSceneIndices.includes(sceneIndex);
    set({
      selectedSceneIndices: exists
        ? selectedSceneIndices.filter((i) => i !== sceneIndex)
        : [...selectedSceneIndices, sceneIndex],
      lastSelectedIndex: sceneIndex,
    });
  },
  clearSelection: () => set({ selectedSceneIndices: [], lastSelectedIndex: null }),
  setMergePreview: (mergePreview) => set({ mergePreview }),
  setAnalysisStage: (analysisStage) => set({ analysisStage }),
  setUploadVideoMeta: (uploadVideoMeta) => set({ uploadVideoMeta }),
  setUploadAudioMeta: (uploadAudioMeta) => set({ uploadAudioMeta }),
  reset: () => set({ ...initial }),
}));
