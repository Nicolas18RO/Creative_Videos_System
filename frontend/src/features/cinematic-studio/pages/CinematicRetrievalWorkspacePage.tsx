import "../styles/cinematic-studio.css";

import { useCallback, useEffect, useMemo, useState } from "react";

import { AnalyzeUploadPanel } from "../export/components/AnalyzeUploadPanel";
import { ExportPipelinePanel } from "../export/components/ExportPipelinePanel";
import { saveStudioSession } from "../export/services/studioSessionPersistence";
import { PlaybackStudioPanel } from "../playback/components/PlaybackStudioPanel";
import { ProjectTimelinePanel } from "../timeline/components/ProjectTimelinePanel";
import { useTimelineEngineStore } from "../timeline/state/timelineEngineStore";

import { ApiHealthBanner } from "../components/ApiHealthBanner";
import { ClipCandidateStrip } from "../components/ClipCandidateStrip";
import { LibraryExplorer } from "../components/LibraryExplorer";
import { ProjectSceneRail } from "../components/ProjectSceneRail";
import { SceneGapPanel } from "../components/SceneGapPanel";
import { SceneScriptPanel } from "../components/SceneScriptPanel";
import { ClipOrganizationPanel } from "../organization/components/ClipOrganizationPanel";
import { useClipFeedback } from "../hooks/useClipFeedback";
import { useLibraryExplorer } from "../hooks/useLibraryExplorer";
import { useSceneRetrieval } from "../hooks/useSceneRetrieval";
import { useStudioBootstrap } from "../hooks/useStudioBootstrap";
import { useStudioProject } from "../hooks/useStudioProject";
import { usePlaybackStore } from "../playback/state/playbackStore";
import { useStudioStore } from "../state/studioStore";
import type { ClipSummaryDto } from "../types/studio";

type Props = {
  onOpenTraining?: () => void;
};

export function CinematicRetrievalWorkspacePage({ onOpenTraining }: Props) {
  const { loadProject, refreshProject } = useStudioProject();

  const handleRestoreProject = useCallback(
    (projectId: string, sceneId: string | null) => {
      void loadProject(projectId, sceneId);
    },
    [loadProject],
  );

  const { reload: reloadBootstrap } = useStudioBootstrap({
    onRestoreProject: handleRestoreProject,
  });
  const { researchScene, clearPreviewSearch } = useSceneRetrieval();
  const { submitFeedback } = useClipFeedback();
  const { loadMore, reloadFirstPage, manualSearch, exploreSimilarToClip } = useLibraryExplorer();

  const projects = useStudioStore((s) => s.projects);
  const projectDetail = useStudioStore((s) => s.projectDetail);
  const gaps = useStudioStore((s) => s.gaps);
  const selectedProjectId = useStudioStore((s) => s.selectedProjectId);
  const selectedSceneId = useStudioStore((s) => s.selectedSceneId);
  const selectScene = useStudioStore((s) => s.selectScene);
  const candidateMode = useStudioStore((s) => s.candidateMode);
  const previewSearchResults = useStudioStore((s) => s.previewSearchResults);
  const libraryExploreCandidates = useStudioStore((s) => s.libraryExploreCandidates);
  const libraryStats = useStudioStore((s) => s.libraryStats);
  const libraryClips = useStudioStore((s) => s.libraryClips);
  const libraryLoaded = useStudioStore((s) => s.libraryLoaded);
  const libraryTotal = useStudioStore((s) => s.libraryTotal);
  const inspectedLibraryClip = useStudioStore((s) => s.inspectedLibraryClip);
  const busy = useStudioStore((s) => s.busy);
  const error = useStudioStore((s) => s.error);
  const setError = useStudioStore((s) => s.setError);

  const [librarySearchQuery, setLibrarySearchQuery] = useState("");
  const [playbackRefreshKey, setPlaybackRefreshKey] = useState(0);

  const selectedScene = useMemo(
    () => projectDetail?.scenes.find((s) => s.scene_id === selectedSceneId) ?? null,
    [projectDetail, selectedSceneId],
  );

  const gapForScene = useMemo(() => {
    if (!selectedSceneId || !gaps) return null;
    const item = gaps.gaps.find((g) => g.gap.scene_id === selectedSceneId);
    return item?.gap ?? null;
  }, [gaps, selectedSceneId]);

  const explorationHint = inspectedLibraryClip
    ? "Exploración de biblioteca: los gaps M3 se generan al analizar un guion; aquí inspeccionas el clip y vecinos semánticos."
    : null;

  const handleSelectProject = useCallback(
    (id: string) => {
      void loadProject(id);
    },
    [loadProject],
  );

  const handleSelectScene = useCallback(
    (sceneId: string) => {
      selectScene(sceneId);
      const sc = projectDetail?.scenes.find((s) => s.scene_id === sceneId);
      if (sc) {
        useTimelineEngineStore.getState().selectScene(sc.scene_index);
        usePlaybackStore.getState().orchestrator?.selectScene(sc.scene_index, "timeline");
      }
      const pid = useStudioStore.getState().selectedProjectId;
      saveStudioSession({ projectId: pid, sceneId });
    },
    [projectDetail, selectScene],
  );

  const handlePlaybackSceneIndex = useCallback(
    (idx: number) => {
      const sc = projectDetail?.scenes.find((s) => s.scene_index === idx);
      if (sc) handleSelectScene(sc.scene_id);
    },
    [projectDetail?.scenes, handleSelectScene],
  );

  const handleAnalyzeProjectCreated = useCallback(
    (id: string) => {
      void loadProject(id);
    },
    [loadProject],
  );

  const handleExportRestored = useCallback(() => {
    void refreshProject();
    setPlaybackRefreshKey((k) => k + 1);
  }, [refreshProject]);

  useEffect(() => {
    if (!selectedScene) return;
    useTimelineEngineStore.getState().selectScene(selectedScene.scene_index);
  }, [selectedScene?.scene_id, selectedScene?.scene_index]);

  const handleFeedback = useCallback(
    async (sceneId: string, clipId: string, accepted: boolean, rank: number) => {
      setError(null);
      try {
        await submitFeedback(sceneId, clipId, accepted, rank);
        clearPreviewSearch();
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
      }
    },
    [clearPreviewSearch, setError, submitFeedback],
  );

  const handleLibrarySearch = useCallback(() => {
    void manualSearch(librarySearchQuery);
  }, [librarySearchQuery, manualSearch]);

  const handleActivateClip = useCallback(
    (clip: ClipSummaryDto) => {
      void exploreSimilarToClip(clip);
    },
    [exploreSimilarToClip],
  );

  const showLibraryCandidates =
    candidateMode === "library_explore" && libraryExploreCandidates !== null;

  return (
    <div className="cs-root">
      <div className="cs-shell">
        <header className="cs-hero">
          <div>
            <h1>Cinematic Retrieval Studio</h1>
            <p>
              Selección de clips, búsqueda semántica y feedback humano — migración Phase 7.1 desde el dashboard
              PyQt. Toda la inteligencia vive en FastAPI.
            </p>
          </div>
          <div className="cs-hero__actions">
            {onOpenTraining && (
              <button type="button" className="cs-btn cs-btn--ghost" onClick={onOpenTraining}>
                Entrenamiento editorial →
              </button>
            )}
            <button type="button" className="cs-btn cs-btn--ghost" disabled={busy} onClick={() => void reloadBootstrap()}>
              Recargar biblioteca
            </button>
          </div>
        </header>

        <ApiHealthBanner />

        {error && (
          <div className="cs-banner cs-banner--warn" role="alert">
            {error}
          </div>
        )}

        <AnalyzeUploadPanel disabled={busy} onProjectCreated={handleAnalyzeProjectCreated} />

        <ExportPipelinePanel projectId={selectedProjectId} onRestored={handleExportRestored} />

        <PlaybackStudioPanel
          projectId={selectedProjectId}
          sessionRefreshKey={playbackRefreshKey}
          onSceneIndex={handlePlaybackSceneIndex}
        />

        <ProjectTimelinePanel
          projectId={selectedProjectId}
          onTimelineMutated={() => {
            void refreshProject();
            setPlaybackRefreshKey((k) => k + 1);
          }}
          onSceneSelected={(sceneId) => handleSelectScene(sceneId)}
        />

        <div className="cs-workspace">
          <LibraryExplorer
            stats={libraryStats}
            clips={libraryClips}
            loaded={libraryLoaded}
            total={libraryTotal}
            searchQuery={librarySearchQuery}
            onSearchQueryChange={setLibrarySearchQuery}
            onSearch={handleLibrarySearch}
            onLoadMore={() => void loadMore()}
            onActivateClip={handleActivateClip}
            busy={busy}
          />

          <main className="cs-main">
            <div className="cs-main__triple">
              <SceneScriptPanel scene={selectedScene} inspectedClip={inspectedLibraryClip} />
              <ClipCandidateStrip
                scene={showLibraryCandidates ? null : selectedScene}
                mode={candidateMode}
                previewResults={previewSearchResults}
                libraryExploreResults={libraryExploreCandidates}
                busy={busy}
                onAccept={(sid, cid, rank) => void handleFeedback(sid, cid, true, rank)}
                onReject={(sid, cid, rank) => void handleFeedback(sid, cid, false, rank)}
              />
              <SceneGapPanel gap={gapForScene} explorationHint={explorationHint} />
            </div>

            <ClipOrganizationPanel
              clip={inspectedLibraryClip}
              onApplied={() => void reloadFirstPage()}
            />

            <div className="cs-main__toolbar">
              <button
                type="button"
                className="cs-btn"
                disabled={!selectedScene || busy}
                onClick={() => void researchScene()}
              >
                Re-buscar clips para escena
              </button>
              {candidateMode === "preview_search" && (
                <button type="button" className="cs-btn cs-btn--ghost" disabled={busy} onClick={clearPreviewSearch}>
                  Volver a recomendaciones persistidas
                </button>
              )}
            </div>

            <ProjectSceneRail
              projects={projects.map((p) => ({ id: p.id, name: p.name }))}
              selectedProjectId={selectedProjectId}
              detail={projectDetail}
              gaps={gaps}
              selectedSceneId={selectedSceneId}
              onSelectProject={handleSelectProject}
              onSelectScene={handleSelectScene}
              onRefreshProjects={() => void reloadBootstrap()}
            />
          </main>
        </div>

        <p className="cs-footnote">
          Organización M4: preview en Studio, apply solo con confirmación. El dashboard PyQt sigue disponible.
        </p>
      </div>
    </div>
  );
}
