import { create } from "zustand";

import type {
  CandidateSourceMode,
  ClipSummaryDto,
  ProjectDetailDto,
  ProjectGapsDto,
  ProjectSummaryDto,
  RecommendationDto,
} from "../types/studio";

type StudioStore = {
  projects: ProjectSummaryDto[];
  projectDetail: ProjectDetailDto | null;
  gaps: ProjectGapsDto | null;
  selectedProjectId: string | null;
  selectedSceneId: string | null;
  candidateMode: CandidateSourceMode;
  previewSearchResults: RecommendationDto[] | null;
  libraryStats: { total_clips: number; naming_compliant: number } | null;
  libraryClips: ClipSummaryDto[];
  libraryTotal: number;
  libraryLoaded: number;
  libraryPageSize: number;
  inspectedLibraryClip: ClipSummaryDto | null;
  libraryExploreCandidates: RecommendationDto[] | null;
  busy: boolean;
  error: string | null;
  healthOk: boolean | null;
  setProjects: (p: ProjectSummaryDto[]) => void;
  setProjectDetail: (d: ProjectDetailDto | null) => void;
  setGaps: (g: ProjectGapsDto | null) => void;
  selectProject: (id: string | null) => void;
  selectScene: (sceneId: string | null) => void;
  setCandidateMode: (m: CandidateSourceMode) => void;
  setPreviewSearchResults: (r: RecommendationDto[] | null) => void;
  clearPreviewSearch: () => void;
  setLibraryStats: (s: { total_clips: number; naming_compliant: number } | null) => void;
  setLibraryPage: (items: ClipSummaryDto[], total: number, loaded: number) => void;
  appendLibraryClips: (items: ClipSummaryDto[], loaded: number) => void;
  resetLibraryList: () => void;
  setInspectedLibraryClip: (c: ClipSummaryDto | null) => void;
  setLibraryExploreCandidates: (r: RecommendationDto[] | null) => void;
  setBusy: (b: boolean) => void;
  setError: (e: string | null) => void;
  setHealthOk: (ok: boolean | null) => void;
  resetWorkspace: () => void;
};

export const useStudioStore = create<StudioStore>((set) => ({
  projects: [],
  projectDetail: null,
  gaps: null,
  selectedProjectId: null,
  selectedSceneId: null,
  candidateMode: "persisted",
  previewSearchResults: null,
  libraryStats: null,
  libraryClips: [],
  libraryTotal: 0,
  libraryLoaded: 0,
  libraryPageSize: 50,
  inspectedLibraryClip: null,
  libraryExploreCandidates: null,
  busy: false,
  error: null,
  healthOk: null,
  setProjects: (projects) => set({ projects }),
  setProjectDetail: (projectDetail) => set({ projectDetail }),
  setGaps: (gaps) => set({ gaps }),
  selectProject: (selectedProjectId) =>
    set({
      selectedProjectId,
      selectedSceneId: null,
      projectDetail: null,
      gaps: null,
      candidateMode: "persisted",
      previewSearchResults: null,
    }),
  selectScene: (selectedSceneId) =>
    set({
      selectedSceneId,
      candidateMode: "persisted",
      previewSearchResults: null,
      inspectedLibraryClip: null,
      libraryExploreCandidates: null,
    }),
  setCandidateMode: (candidateMode) => set({ candidateMode }),
  setPreviewSearchResults: (previewSearchResults) =>
    set({ previewSearchResults, candidateMode: "preview_search" }),
  clearPreviewSearch: () => set({ previewSearchResults: null, candidateMode: "persisted" }),
  setLibraryStats: (libraryStats) => set({ libraryStats }),
  setLibraryPage: (items, libraryTotal, libraryLoaded) =>
    set({ libraryClips: items, libraryTotal, libraryLoaded }),
  appendLibraryClips: (items, libraryLoaded) =>
    set((s) => ({ libraryClips: [...s.libraryClips, ...items], libraryLoaded })),
  resetLibraryList: () => set({ libraryClips: [], libraryTotal: 0, libraryLoaded: 0 }),
  setInspectedLibraryClip: (inspectedLibraryClip) => set({ inspectedLibraryClip }),
  setLibraryExploreCandidates: (libraryExploreCandidates) =>
    set({ libraryExploreCandidates, candidateMode: "library_explore" }),
  setBusy: (busy) => set({ busy }),
  setError: (error) => set({ error }),
  setHealthOk: (healthOk) => set({ healthOk }),
  resetWorkspace: () =>
    set({
      projectDetail: null,
      gaps: null,
      selectedProjectId: null,
      selectedSceneId: null,
      candidateMode: "persisted",
      previewSearchResults: null,
      inspectedLibraryClip: null,
      libraryExploreCandidates: null,
      error: null,
    }),
}));
