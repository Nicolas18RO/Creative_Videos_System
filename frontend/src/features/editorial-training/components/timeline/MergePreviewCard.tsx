import { memo } from "react";

import { mediaSrc } from "../../api/timelineVisualizationApi";
import { formatTimelineTime } from "../../services/timelineTimeFormat";
import type { MergePreviewResultDto } from "../../types/timelinePrecision";
import type { EditableScene } from "../../types/trainingWorkspace";

type Props = {
  preview: MergePreviewResultDto;
  sceneA?: EditableScene;
  sceneB?: EditableScene;
  merging?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
};

function SliceRow({
  label,
  slice,
  thumb,
}: {
  label: string;
  slice: MergePreviewResultDto["scene_a"];
  thumb?: string;
}) {
  return (
    <div className="et-merge-slice">
      {thumb ? <img src={thumb} alt="" className="et-merge-slice__thumb" loading="lazy" /> : <div className="et-merge-slice__ph">{label}</div>}
      <div>
        <strong>{label}</strong>
        <p className="et-mono et-muted">
          {formatTimelineTime(slice.start_time)} → {formatTimelineTime(slice.end_time)}
        </p>
        <p className="et-muted">{slice.duration.toFixed(3)}s · {slice.narrative_role}</p>
      </div>
    </div>
  );
}

export const MergePreviewCard = memo(function MergePreviewCard({
  preview,
  sceneA,
  sceneB,
  merging,
  onConfirm,
  onCancel,
}: Props) {
  const thumbA = mediaSrc(sceneA?.thumbnail_url ?? "");
  const thumbB = mediaSrc(sceneB?.thumbnail_url ?? "");

  return (
    <div className="et-modal-backdrop et-modal-backdrop--merge">
      <div className="et-modal et-modal--wide" role="dialog" aria-modal="true">
        <h3>Vista previa de fusión</h3>
        <p className="et-muted">
          Límite eliminado: <span className="et-mono">{formatTimelineTime(preview.removed_boundary_time)}</span>
        </p>

        <div className="et-merge-equation">
          <SliceRow label={`Escena ${preview.scene_a.scene_index}`} slice={preview.scene_a} thumb={thumbA} />
          <span className="et-merge-op">+</span>
          <SliceRow label={`Escena ${preview.scene_b.scene_index}`} slice={preview.scene_b} thumb={thumbB} />
          <span className="et-merge-op">=</span>
          <SliceRow label="Escena fusionada" slice={preview.merged} />
        </div>

        <p className="et-merge-total">
          Duración total: <strong>{preview.total_duration.toFixed(3)}s</strong>
        </p>

        {merging ? (
          <p className="et-merge-loading">
            <span className="et-spinner" aria-hidden /> Fusionando escenas…
          </p>
        ) : null}

        <div className="et-inline" style={{ marginTop: 16 }}>
          <button type="button" className="et-btn et-btn--primary" disabled={merging} onClick={onConfirm}>
            Confirmar fusión
          </button>
          <button type="button" className="et-btn et-btn--ghost" disabled={merging} onClick={onCancel}>
            Cancelar
          </button>
        </div>
      </div>
    </div>
  );
});
