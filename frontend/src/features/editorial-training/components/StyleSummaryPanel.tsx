import { useTrainingWorkspaceStore } from "../state/trainingWorkspaceStore";

export function StyleSummaryPanel() {
  const summary = useTrainingWorkspaceStore((s) => s.workspace?.summary);

  if (!summary) {
    return (
      <section className="et-card">
        <h2>Paso 6 — Resumen de aprendizaje</h2>
        <p className="et-muted">El resumen aparecerá cuando exista un timeline analizado.</p>
      </section>
    );
  }

  return (
    <section className="et-card">
      <h2>Paso 6 — Resumen de aprendizaje</h2>
      <div className="et-summary-grid">
        <div className="et-kpi">
          <span>Escenas totales</span>
          <strong>{summary.total_scenes}</strong>
        </div>
        <div className="et-kpi">
          <span>Hooks detectados</span>
          <strong>{summary.hooks_detected}</strong>
        </div>
        <div className="et-kpi">
          <span>Pacing (score)</span>
          <strong>{summary.pacing_score.toFixed(2)}</strong>
        </div>
        <div className="et-kpi">
          <span>Pacing medio (perfil)</span>
          <strong>{summary.average_pacing.toFixed(2)}</strong>
        </div>
        <div className="et-kpi">
          <span>Densidad de movimiento</span>
          <strong>{summary.motion_density.toFixed(2)}</strong>
        </div>
        <div className="et-kpi">
          <span>Dinamismo visual</span>
          <strong>{summary.style_visual_dynamism.toFixed(2)}</strong>
        </div>
        <div className="et-kpi">
          <span>Correcciones aplicadas</span>
          <strong>{summary.corrections_applied}</strong>
        </div>
        <div className="et-kpi">
          <span>Aceptaciones / rechazos</span>
          <strong>
            {summary.clip_accept_count} / {summary.clip_reject_count}
          </strong>
        </div>
      </div>
    </section>
  );
}
