import { useEffect, useState } from "react";

import { msFromSec, secFromMs } from "../presentation/timelineEnginePresentation";
import type { ProjectTimelineSceneDto } from "../types/timelineEngine";

type Props = {
  scene: ProjectTimelineSceneDto | null;
  syncing: boolean;
  onTrim: (sceneId: string, startMs: number, endMs: number) => void;
  onSplit: (sceneId: string, splitAtMs: number) => void;
  onReplaceClip: (sceneId: string, clipId: string) => void;
};

export function StudioSceneMutationPanel({ scene, syncing, onTrim, onSplit, onReplaceClip }: Props) {
  const [trimIn, setTrimIn] = useState("");
  const [trimOut, setTrimOut] = useState("");
  const [splitPct, setSplitPct] = useState("50");
  const [clipId, setClipId] = useState("");

  useEffect(() => {
    if (!scene) return;
    setTrimIn(secFromMs(scene.start_ms).toFixed(2));
    setTrimOut(secFromMs(scene.end_ms).toFixed(2));
    setClipId(scene.selected_clip_id ?? "");
  }, [scene?.scene_id, scene?.start_ms, scene?.end_ms, scene?.selected_clip_id]);

  if (!scene) {
    return (
      <div className="cs-tl-mutate cs-tl-mutate--empty">
        <p className="cs-muted">Selecciona una escena en el timeline para recortar, dividir o reemplazar clip.</p>
      </div>
    );
  }

  return (
    <div className="cs-tl-mutate">
      <h3>Edición · escena #{scene.scene_index}</h3>
      <div className="cs-tl-mutate__grid">
        <label>
          IN (s)
          <input
            className="cs-input"
            type="number"
            step={0.01}
            value={trimIn}
            disabled={syncing}
            onChange={(e) => setTrimIn(e.target.value)}
          />
        </label>
        <label>
          OUT (s)
          <input
            className="cs-input"
            type="number"
            step={0.01}
            value={trimOut}
            disabled={syncing}
            onChange={(e) => setTrimOut(e.target.value)}
          />
        </label>
        <button
          type="button"
          className="cs-btn"
          disabled={syncing}
          onClick={() =>
            onTrim(scene.scene_id, msFromSec(parseFloat(trimIn)), msFromSec(parseFloat(trimOut)))
          }
        >
          Aplicar trim
        </button>
      </div>
      <div className="cs-tl-mutate__grid">
        <label>
          Split (%)
          <input
            className="cs-input"
            type="number"
            min={5}
            max={95}
            value={splitPct}
            disabled={syncing}
            onChange={(e) => setSplitPct(e.target.value)}
          />
        </label>
        <button
          type="button"
          className="cs-btn cs-btn--ghost"
          disabled={syncing}
          onClick={() => {
            const pct = Math.min(95, Math.max(5, parseFloat(splitPct) || 50)) / 100;
            const at = scene.start_ms + Math.round(scene.duration_ms * pct);
            onSplit(scene.scene_id, at);
          }}
        >
          Dividir escena
        </button>
      </div>
      <div className="cs-tl-mutate__grid">
        <label>
          Clip ID
          <input
            className="cs-input"
            value={clipId}
            disabled={syncing}
            onChange={(e) => setClipId(e.target.value)}
            placeholder="UUID del clip"
          />
        </label>
        <button
          type="button"
          className="cs-btn"
          disabled={syncing || !clipId.trim()}
          onClick={() => onReplaceClip(scene.scene_id, clipId.trim())}
        >
          Insertar / reemplazar clip
        </button>
      </div>
    </div>
  );
}
