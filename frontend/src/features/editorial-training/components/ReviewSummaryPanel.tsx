import { useEffect } from "react";

import { useTrainingWorkspaceStore } from "../state/trainingWorkspaceStore";
import { useEditorialReview } from "../hooks/useEditorialReview";

type Props = {
  disabled?: boolean;
  onRefreshWorkspace: () => Promise<void>;
};

export function ReviewSummaryPanel({ disabled, onRefreshWorkspace }: Props) {
  const reviewSummary = useTrainingWorkspaceStore((s) => s.reviewSummary);
  const scenes = useTrainingWorkspaceStore((s) => s.sceneDrafts);
  const { runBulkAction, reloadSummary } = useEditorialReview();

  useEffect(() => {
    void reloadSummary();
  }, [reloadSummary]);

  const pendingScenes = scenes.filter((s) => s.review_status === "pending");

  return (
    <section className="et-card">
      <h2>Paso 5 — Review Summary</h2>
      <p className="et-muted">
        Resumen de revisión humana. Las acciones principales están en el timeline (paso 4). Aquí solo pendientes,
        advertencias y acciones masivas.
      </p>

      {reviewSummary ? (
        <div className="et-summary-grid" style={{ marginTop: 14 }}>
          <div className="et-kpi">
            <span>Pendientes</span>
            <strong>{reviewSummary.pending}</strong>
          </div>
          <div className="et-kpi">
            <span>Aceptadas</span>
            <strong>{reviewSummary.accepted}</strong>
          </div>
          <div className="et-kpi">
            <span>Rechazadas</span>
            <strong>{reviewSummary.rejected}</strong>
          </div>
          <div className="et-kpi">
            <span>Fusionadas</span>
            <strong>{reviewSummary.merged}</strong>
          </div>
        </div>
      ) : null}

      {reviewSummary?.warnings?.length ? (
        <ul className="et-warnings" style={{ marginTop: 12 }}>
          {reviewSummary.warnings.map((w) => (
            <li key={w}>{w}</li>
          ))}
        </ul>
      ) : null}

      <div className="et-inline" style={{ marginTop: 14, flexWrap: "wrap" }}>
        <button type="button" className="et-btn et-btn--ok" disabled={disabled} onClick={() => void runBulkAction("accept_all_pending")}>
          Aceptar todas pendientes
        </button>
        <button type="button" className="et-btn et-btn--danger" disabled={disabled} onClick={() => void runBulkAction("reject_all_pending")}>
          Rechazar todas pendientes
        </button>
        <button type="button" className="et-btn et-btn--ghost" disabled={disabled} onClick={() => void runBulkAction("accept_high_confidence", 0.75)}>
          Auto-aceptar alta confianza
        </button>
        <button type="button" className="et-btn et-btn--ghost" disabled={disabled} onClick={() => void runBulkAction("reset_review_states")}>
          Reset estados
        </button>
        <button
          type="button"
          className="et-btn et-btn--ghost"
          disabled={disabled}
          onClick={() => {
            void reloadSummary();
            void onRefreshWorkspace();
          }}
        >
          Actualizar resumen
        </button>
      </div>

      {pendingScenes.length > 0 ? (
        <div style={{ marginTop: 16 }}>
          <h3 style={{ fontSize: "0.95rem", margin: "0 0 8px" }}>Escenas pendientes ({pendingScenes.length})</h3>
          <ul className="et-pending-list">
            {pendingScenes.slice(0, 12).map((s) => (
              <li key={s.scene_index}>
                #{s.scene_index} · {s.scene_type_label} · conf. {((s.confidence_score ?? 0) * 100).toFixed(0)}%
              </li>
            ))}
            {pendingScenes.length > 12 ? <li className="et-muted">… y {pendingScenes.length - 12} más en el timeline</li> : null}
          </ul>
        </div>
      ) : (
        <p className="et-success" style={{ marginTop: 14 }}>
          No hay escenas pendientes. Puedes continuar al resumen de aprendizaje (paso 6).
        </p>
      )}
    </section>
  );
}
