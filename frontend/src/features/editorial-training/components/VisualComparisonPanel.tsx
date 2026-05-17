import { mediaSrc } from "../api/timelineVisualizationApi";
import type { EditableScene } from "../types/trainingWorkspace";

type Props = {
  scene: EditableScene | null;
  compareClipId: string;
};

export function VisualComparisonPanel({ scene, compareClipId }: Props) {
  if (!scene) {
    return <div className="vt-compare vt-compare--empty">Modo A/B: selecciona una escena</div>;
  }

  const aThumb = mediaSrc(scene.thumbnail_url);
  const bLabel = compareClipId || "Sin clip alternativo";

  return (
    <div className="vt-compare">
      <h3 className="vt-compare__title">Comparación A / B</h3>
      <div className="vt-compare__grid">
        <div className="vt-compare__pane">
          <span className="vt-compare__tag">A · Timeline actual</span>
          {aThumb ? <img src={aThumb} alt="" className="vt-compare__img" loading="lazy" /> : <div className="vt-compare__ph">Sin thumb</div>}
          <p>{scene.clip_id}</p>
        </div>
        <div className="vt-compare__pane">
          <span className="vt-compare__tag">B · Corrección propuesta</span>
          <div className="vt-compare__ph">{bLabel}</div>
          <p className="et-muted">Asigna un clip de biblioteca en correcciones o reemplaza la escena.</p>
        </div>
      </div>
    </div>
  );
}
