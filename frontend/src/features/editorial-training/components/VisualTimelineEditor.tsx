import { useCallback, useEffect, useMemo, useState } from "react";

import { useVisualTimeline } from "../hooks/useVisualTimeline";
import { useEditorialReview } from "../hooks/useEditorialReview";
import { useTimelineDraft } from "../hooks/useTimelineDraft";
import { useTrainingWorkspaceStore } from "../state/trainingWorkspaceStore";
import { useTimelineDraftStore } from "../state/timelineDraftStore";
import { ScenePreviewPlayer } from "./ScenePreviewPlayer";
import { TimelineHeatmap } from "./TimelineHeatmap";
import { TimelineReviewToolbar } from "./TimelineReviewToolbar";
import { TimelineWorkspace } from "./TimelineWorkspace";
import { VisualComparisonPanel } from "./VisualComparisonPanel";
import { VisualTimelineTrack } from "./VisualTimelineTrack";
import { TimelineDraftToolbar } from "./timeline/TimelineDraftToolbar";

type Props = {
  creativeId: string | null;
  onReloadSession: (sessionId: string) => Promise<void>;
};

export function VisualTimelineEditor({ creativeId, onReloadSession }: Props) {
  const workspaceScenes = useTrainingWorkspaceStore((s) => s.sceneDrafts);
  const sessionId = useTrainingWorkspaceStore((s) => s.sessionId);
  const loading = useTrainingWorkspaceStore((s) => s.loading);
  const draftScenes = useTimelineDraftStore((s) => s.draftScenes);
  const initFromScenes = useTimelineDraftStore((s) => s.initFromScenes);
  const { visual, load, regenerate } = useVisualTimeline();
  const { reloadSummary } = useEditorialReview();
  const { saveDraft, validateDraft } = useTimelineDraft();

  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);
  const [zoom, setZoom] = useState(1.2);
  const [compareClipId, setCompareClipId] = useState("");

  useEffect(() => {
    if (workspaceScenes.length) initFromScenes(workspaceScenes);
  }, [workspaceScenes, initFromScenes]);

  const activeScenes = useMemo(
    () => draftScenes.filter((s) => s.review_status !== "merged"),
    [draftScenes],
  );

  useEffect(() => {
    if (creativeId) void load(creativeId);
  }, [creativeId, load]);

  useEffect(() => {
    if (sessionId && creativeId) void reloadSummary();
  }, [sessionId, creativeId, reloadSummary]);

  const selected = useMemo(
    () => activeScenes.find((s) => s.scene_index === selectedIndex) ?? activeScenes[0] ?? null,
    [activeScenes, selectedIndex],
  );

  const handleReorder = useCallback(
    (from: number, to: number) => {
      const sorted = [...activeScenes].sort((a, b) => a.scene_index - b.scene_index);
      const fromPos = sorted.findIndex((s) => s.scene_index === from);
      const toPos = sorted.findIndex((s) => s.scene_index === to);
      if (fromPos < 0 || toPos < 0) return;
      const next = [...sorted];
      const [item] = next.splice(fromPos, 1);
      next.splice(toPos, 0, item);
      const reindexed = next.map((s, i) => ({ ...s, scene_index: i }));
      useTimelineDraftStore.getState().initFromScenes(reindexed);
    },
    [activeScenes],
  );

  return (
    <section className="vt-editor">
      <header className="vt-editor__head">
        <div>
          <h2>Timeline cinematográfico — edición precisa</h2>
          <p className="et-muted">Recorta IN/OUT, fusiona con vista previa y guarda ajustes sin sobrescribir la detección automática.</p>
        </div>
        <div className="et-inline">
          <label className="et-label">Zoom</label>
          <input type="range" min={0.8} max={2.5} step={0.1} value={zoom} onChange={(e) => setZoom(Number(e.target.value))} />
          <button type="button" className="et-btn et-btn--ghost" disabled={!creativeId} onClick={() => creativeId && void regenerate(creativeId, true)}>
            Regenerar previews
          </button>
        </div>
      </header>

      <TimelineDraftToolbar
        disabled={loading}
        onValidate={() => void validateDraft()}
        onSave={() => sessionId && void saveDraft((id) => onReloadSession(id))}
      />

      <TimelineReviewToolbar disabled={loading} />

      <VisualTimelineTrack
        track={visual?.track ?? null}
        scenes={activeScenes}
        selectedIndex={selected?.scene_index ?? null}
        zoom={zoom}
        onSelect={setSelectedIndex}
        onReorder={handleReorder}
      />

      <TimelineHeatmap track={visual?.track ?? null} selectedIndex={selected?.scene_index ?? null} onSelect={setSelectedIndex} />

      <div className="vt-editor__split">
        <ScenePreviewPlayer scene={selected} />
        <VisualComparisonPanel scene={selected} compareClipId={compareClipId} />
      </div>

      {selected ? (
        <div className="et-card">
          <label className="et-label">Clip B (comparación)</label>
          <input className="et-input" value={compareClipId} onChange={(e) => setCompareClipId(e.target.value)} placeholder="clip_id alternativo" />
        </div>
      ) : null}

      <TimelineWorkspace />
    </section>
  );
}
