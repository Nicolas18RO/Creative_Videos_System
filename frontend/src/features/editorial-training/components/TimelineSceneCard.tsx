import { mediaSrc } from "../api/timelineVisualizationApi";
import type { EditableScene, ReviewStatus } from "../types/trainingWorkspace";
import { visualEnergyToLabel } from "../services/sceneDraftMapper";
import { SceneAudioContextBanner } from "./timeline/SceneAudioContextBanner";
import { SemanticIntentPanel } from "./timeline/SemanticIntentPanel";
import { narrativeColor } from "../services/narrativeColors";
import { ReviewStatusBadge } from "./ReviewStatusBadge";
import { TimelineBoundaryEditor } from "./timeline/TimelineBoundaryEditor";

type Props = {
  scene: EditableScene;
  disabled?: boolean;
  selected?: boolean;
  timelineDuration?: number;
  validationMessage?: string | null;
  onSelect: (shift: boolean) => void;
  onPatch: (patch: Partial<EditableScene>) => void;
  onTimingChange: (start: number, end: number) => void;
  onResetScene: () => void;
  onAccept: () => void;
  onReject: () => void;
  onMergeNext?: (anchor: HTMLElement) => void;
  onRestore?: () => void;
};

export function TimelineSceneCard({
  scene,
  disabled,
  selected,
  onSelect,
  onPatch,
  onTimingChange,
  onResetScene,
  timelineDuration = 60,
  validationMessage,
  onAccept,
  onReject,
  onMergeNext,
  onRestore,
}: Props) {
  const transitions = ["cut", "dissolve", "whip_pan", "motion_blur", "match_cut"];
  const thumb = mediaSrc(scene.thumbnail_url);
  const preview = mediaSrc(scene.preview_video_url);
  const displayIntent = scene.narrative_intent || scene.narrative_role;
  const border = narrativeColor(displayIntent);
  const status = (scene.review_status || "pending") as ReviewStatus;
  const isMerged = status === "merged";

  return (
    <article
      className={`et-scene et-scene--${status} ${selected ? "et-scene--selected" : ""}`}
      style={{ borderLeftColor: border, opacity: isMerged ? 0.55 : 1 }}
      onClick={(e) => onSelect(e.shiftKey)}
    >
      <div className="et-thumb">
        {thumb ? <img src={thumb} alt="" loading="lazy" className="et-thumb__img" /> : <span className="et-thumb__ph">#{scene.scene_index}</span>}
        <ReviewStatusBadge status={status} />
        <span className="et-thumb__hook">{((scene.confidence_score ?? 0) * 100).toFixed(0)}%</span>
      </div>
      <div>
        <div className="et-scene-head">
          <div>
            <strong style={{ color: "#f8fafc" }}>{scene.scene_type_label}</strong>
            <div className="et-muted" style={{ marginTop: 4, fontSize: 12 }}>
              Clip: {scene.clip_source_taxonomy || scene.auto_clip_source_taxonomy || "—"} · Narrativa: {displayIntent}
            </div>
            <div className="et-muted" style={{ marginTop: 4 }}>
              {scene.time_start.toFixed(2)}s → {scene.time_end.toFixed(2)}s · {scene.duration_seconds.toFixed(2)}s
            </div>
          </div>
          <span className="et-badge">Conf. {((scene.confidence_score ?? 0) * 100).toFixed(0)}%</span>
        </div>
        {preview && !isMerged ? (
          <video className="et-scene__preview" src={preview} muted playsInline preload="none" onMouseEnter={(e) => void e.currentTarget.play()} onMouseLeave={(e) => { e.currentTarget.pause(); e.currentTarget.currentTime = 0; }} />
        ) : null}
        {!isMerged ? (
          <>
            <SceneAudioContextBanner scene={scene} />
            <div onClick={(e) => e.stopPropagation()} style={{ marginTop: 10 }}>
              <TimelineBoundaryEditor
                scene={scene}
                timelineDuration={timelineDuration}
                disabled={disabled}
                validationMessage={validationMessage}
                onTimingChange={onTimingChange}
                onResetScene={onResetScene}
              />
            </div>
            <SemanticIntentPanel scene={scene} disabled={disabled} onPatch={onPatch} />
            <div className="et-row">
              <div className="et-stack">
                <label className="et-label">Energía visual</label>
                <input type="range" min={0} max={1} step={0.01} disabled={disabled} className="et-slider" value={scene.visual_energy} onClick={(e) => e.stopPropagation()} onChange={(e) => { const v = Number(e.target.value); onPatch({ visual_energy: v, energy_label: visualEnergyToLabel(v) }); }} />
              </div>
              <div className="et-stack">
                <label className="et-label">Pacing</label>
                <input type="range" min={0} max={1} step={0.01} disabled={disabled} className="et-slider" value={scene.motion_intensity} onClick={(e) => e.stopPropagation()} onChange={(e) => onPatch({ motion_intensity: Number(e.target.value) })} />
              </div>
              <div className="et-stack">
                <label className="et-label">Transición</label>
                <select className="et-select" disabled={disabled} value={scene.transition_type} onClick={(e) => e.stopPropagation()} onChange={(e) => onPatch({ transition_type: e.target.value })}>
                  {transitions.map((t) => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </select>
              </div>
            </div>
            <div className="et-inline" style={{ marginTop: 10 }} onClick={(e) => e.stopPropagation()}>
              <button type="button" className="et-btn et-btn--ok" disabled={disabled} onClick={onAccept}>Aceptar</button>
              <button type="button" className="et-btn et-btn--danger" disabled={disabled} onClick={onReject}>Rechazar</button>
              {onMergeNext ? (
                <button
                  type="button"
                  className="et-btn et-btn--ghost"
                  disabled={disabled}
                  onClick={(e) => {
                    e.stopPropagation();
                    onMergeNext(e.currentTarget);
                  }}
                >
                  Fusionar con siguiente
                </button>
              ) : null}
              {onRestore && status !== "pending" ? <button type="button" className="et-btn et-btn--ghost" disabled={disabled} onClick={onRestore}>Restaurar</button> : null}
              <span className="et-badge">Clip: {scene.clip_id || "—"}</span>
            </div>
          </>
        ) : (
          <p className="et-muted">Escena fusionada → #{scene.merged_into_scene_id ?? "?"}</p>
        )}
      </div>
    </article>
  );
}
