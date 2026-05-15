import { create } from "zustand";

import type {
  EditableScene,
  EditorialTrainingWorkspaceGetDto,
  TrainingStepId,
} from "../types/trainingWorkspace";

type TrainingWorkspaceState = {
  step: TrainingStepId;
  sessionId: string | null;
  workspace: EditorialTrainingWorkspaceGetDto | null;
  sceneDrafts: EditableScene[];
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
    editorial_status: "pending" as const,
  }));
}

export const useTrainingWorkspaceStore = create<TrainingWorkspaceState>((set) => ({
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
    }),
  patchScene: (sceneIndex, patch) =>
    set((state) => ({
      sceneDrafts: state.sceneDrafts.map((s) => (s.scene_index === sceneIndex ? { ...s, ...patch } : s)),
    })),
  setAnalysisStage: (analysisStage) => set({ analysisStage }),
  setUploadVideoMeta: (uploadVideoMeta) => set({ uploadVideoMeta }),
  setUploadAudioMeta: (uploadAudioMeta) => set({ uploadAudioMeta }),
  reset: () => set({ ...initial }),
}));
