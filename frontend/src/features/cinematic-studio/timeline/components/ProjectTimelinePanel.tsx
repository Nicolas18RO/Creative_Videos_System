import { useMemo, useState } from "react";

import { useProjectTimelineEngine } from "../hooks/useProjectTimelineEngine";
import { useTimelineEngineStore } from "../state/timelineEngineStore";
import { StudioSceneMutationPanel } from "./StudioSceneMutationPanel";
import { StudioTimelineToolbar } from "./StudioTimelineToolbar";
import { StudioTimelineTrack } from "./StudioTimelineTrack";

type Props = {
  projectId: string | null;
  onTimelineMutated?: () => void;
  onSceneSelected?: (sceneId: string, sceneIndex: number) => void;
};

export function ProjectTimelinePanel({ projectId, onTimelineMutated, onSceneSelected }: Props) {
  const [zoom, setZoom] = useState(1);
  const { load, reorder, merge, split, trim, replaceClip } = useProjectTimelineEngine(projectId);

  const draftScenes = useTimelineEngineStore((s) => s.draftScenes);
  const durationSec = useTimelineEngineStore((s) => s.timelineDurationSec);
  const selectedSceneIndex = useTimelineEngineStore((s) => s.selectedSceneIndex);
  const selectScene = useTimelineEngineStore((s) => s.selectScene);
  const syncing = useTimelineEngineStore((s) => s.syncing);
  const mutationError = useTimelineEngineStore((s) => s.mutationError);

  const selectedScene = useMemo(
    () => draftScenes.find((s) => s.scene_index === selectedSceneIndex) ?? null,
    [draftScenes, selectedSceneIndex],
  );

  const wrap = (fn: () => Promise<unknown>) => {
    void fn().then(() => onTimelineMutated?.());
  };

  if (!projectId) {
    return (
      <section className="cs-card cs-tl-panel">
        <p className="cs-muted">Selecciona un proyecto para editar el timeline.</p>
      </section>
    );
  }

  return (
    <section className="cs-card cs-tl-panel">
      <StudioTimelineToolbar
        syncing={syncing}
        selectedSceneIndex={selectedSceneIndex}
        sceneCount={draftScenes.length}
        zoom={zoom}
        onZoomChange={setZoom}
        onMergeWithNext={() => {
          if (selectedSceneIndex === null) return;
          void wrap(() => merge(selectedSceneIndex, selectedSceneIndex + 1));
        }}
        onReload={() => void load()}
      />
      {mutationError && (
        <p className="cs-banner cs-banner--warn" role="alert">
          {mutationError}
        </p>
      )}
      <StudioTimelineTrack
        scenes={draftScenes}
        timelineDurationSec={durationSec}
        selectedSceneIndex={selectedSceneIndex}
        zoom={zoom}
        disabled={syncing}
        onSelect={(idx) => {
          selectScene(idx);
          const sc = draftScenes.find((s) => s.scene_index === idx);
          if (sc) onSceneSelected?.(sc.scene_id, idx);
        }}
        onReorder={(from, to) => void wrap(() => reorder(from, to))}
      />
      <StudioSceneMutationPanel
        scene={selectedScene}
        syncing={syncing}
        onTrim={(sid, a, b) => void wrap(() => trim(sid, a, b))}
        onSplit={(sid, at) => void wrap(() => split(sid, at))}
        onReplaceClip={(sid, cid) => void wrap(() => replaceClip(sid, cid))}
      />
    </section>
  );
}
