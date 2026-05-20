import { memo, useEffect } from "react";
import { createPortal } from "react-dom";

import { mediaSrc } from "../../api/timelineVisualizationApi";
import { useFloatingPopoverPosition } from "../../hooks/useFloatingPopoverPosition";
import { formatTimelineTime } from "../../services/timelineTimeFormat";
import { sceneAudioContextText } from "../../services/sceneAudioContext";
import { narrativeColor } from "../../services/narrativeColors";
import type { MergePreviewResultDto } from "../../types/timelinePrecision";
import type { EditableScene } from "../../types/trainingWorkspace";

type Props = {
  preview: MergePreviewResultDto;
  anchorRect: DOMRect;
  sceneA?: EditableScene;
  sceneB?: EditableScene;
  merging?: boolean;
  mergeError?: string | null;
  onConfirm: () => void;
  onCancel: () => void;
};

function ClipCard({
  label,
  slice,
  scene,
  thumb,
  accent,
}: {
  label: string;
  slice: MergePreviewResultDto["scene_a"];
  scene?: EditableScene;
  thumb?: string;
  accent: string;
}) {
  const audio = scene ? sceneAudioContextText(scene) : "";
  return (
    <article className="et-merge-card" style={{ borderColor: accent }}>
      <div className="et-merge-card__media">
        {thumb ? <img src={thumb} alt="" loading="lazy" /> : <span className="et-merge-card__ph">{label}</span>}
      </div>
      <div className="et-merge-card__body">
        <header className="et-merge-card__head">
          <strong>{label}</strong>
          <span className="et-badge" style={{ borderColor: accent, color: accent }}>
            {slice.narrative_role}
          </span>
        </header>
        <p className="et-mono et-muted et-merge-card__time">
          {formatTimelineTime(slice.start_time)} → {formatTimelineTime(slice.end_time)} · {slice.duration.toFixed(2)}s
        </p>
        {audio ? (
          <p className="et-merge-card__audio">«{audio}»</p>
        ) : (
          <p className="et-muted et-merge-card__audio--empty">Sin transcripción</p>
        )}
        {scene?.clip_id ? <p className="et-muted et-merge-card__clip">Clip: {scene.clip_id}</p> : null}
      </div>
    </article>
  );
}

export const MergeFloatingDialog = memo(function MergeFloatingDialog({
  preview,
  anchorRect,
  sceneA,
  sceneB,
  merging,
  mergeError,
  onConfirm,
  onCancel,
}: Props) {
  const position = useFloatingPopoverPosition(anchorRect, { width: 440, estimatedHeight: 520 });
  const thumbA = mediaSrc(sceneA?.thumbnail_url ?? "");
  const thumbB = mediaSrc(sceneB?.thumbnail_url ?? "");
  const colorA = narrativeColor(sceneA?.narrative_intent || sceneA?.narrative_role || preview.scene_a.narrative_role);
  const colorB = narrativeColor(sceneB?.narrative_intent || sceneB?.narrative_role || preview.scene_b.narrative_role);
  const colorM = narrativeColor(preview.merged.narrative_role);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !merging) onCancel();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [merging, onCancel]);

  if (!position) return null;

  return createPortal(
    <>
      <button type="button" className="et-merge-popover-backdrop" aria-label="Cerrar" disabled={merging} onClick={onCancel} />
      <div
        className="et-merge-popover et-merge-popover--cinematic"
        role="dialog"
        aria-modal="true"
        aria-labelledby="et-merge-popover-title"
        style={{ top: position.top, left: position.left, width: position.width, maxHeight: position.maxHeight }}
        onClick={(e) => e.stopPropagation()}
      >
        <header className="et-merge-popover__head">
          <div>
            <p className="et-merge-popover__eyebrow">Fusión cinematográfica</p>
            <h3 id="et-merge-popover-title">Unir clips adyacentes</h3>
          </div>
          <button type="button" className="et-btn et-btn--ghost et-btn--icon" disabled={merging} onClick={onCancel} aria-label="Cerrar">
            ×
          </button>
        </header>

        <p className="et-merge-popover__boundary">
          Se elimina el corte en <span className="et-mono">{formatTimelineTime(preview.removed_boundary_time)}</span>
          {" · "}
          duración resultante <strong>{preview.total_duration.toFixed(2)}s</strong>
        </p>

        <div className="et-merge-flow">
          <ClipCard label={`Escena ${preview.scene_a.scene_index}`} slice={preview.scene_a} scene={sceneA} thumb={thumbA} accent={colorA} />
          <div className="et-merge-flow__op" aria-hidden>
            <span>+</span>
          </div>
          <ClipCard label={`Escena ${preview.scene_b.scene_index}`} slice={preview.scene_b} scene={sceneB} thumb={thumbB} accent={colorB} />
          <div className="et-merge-flow__op et-merge-flow__op--eq" aria-hidden>
            <span>=</span>
          </div>
          <ClipCard label="Clip fusionado" slice={preview.merged} accent={colorM} />
        </div>

        {mergeError ? (
          <p className="et-merge-popover__error" role="alert">
            {mergeError}
          </p>
        ) : null}

        {merging ? (
          <p className="et-merge-loading">
            <span className="et-spinner" aria-hidden /> Aplicando fusión al timeline…
          </p>
        ) : null}

        <footer className="et-merge-popover__actions">
          <button type="button" className="et-btn et-btn--primary" disabled={merging} onClick={onConfirm}>
            Confirmar fusión
          </button>
          <button type="button" className="et-btn et-btn--ghost" disabled={merging} onClick={onCancel}>
            Cancelar
          </button>
        </footer>
      </div>
    </>,
    document.body,
  );
});
