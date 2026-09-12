import { formatDurationMs } from "../presentation/exportPresentation";
import { useExportPipeline } from "../hooks/useExportPipeline";

type Props = {
  projectId: string | null;
  onRestored?: () => void;
};

export function ExportPipelinePanel({ projectId, onRestored }: Props) {
  const {
    capcut,
    readiness,
    manifestHint,
    snapshots,
    busy,
    error,
    lastWrittenPath,
    saveSnapshot,
    restoreSnapshot,
    writeCapCutToDisk,
    downloadCapCut,
  } = useExportPipeline(projectId);

  if (!projectId) {
    return (
      <section className="cs-card cs-exp-panel">
        <p className="cs-muted">Selecciona un proyecto para exportar timeline y manifests.</p>
      </section>
    );
  }

  return (
    <section className="cs-card cs-exp-panel">
      <header className="cs-exp-panel__head">
        <h2>Export Pipeline</h2>
        <span className="cs-muted">Serialización · snapshots · CapCut manifest</span>
      </header>

      {error && (
        <p className="cs-banner cs-banner--warn" role="alert">
          {error}
        </p>
      )}

      {capcut && readiness && (
        <div className="cs-exp-summary">
          <p>
            <strong>{capcut.project_name}</strong> · {formatDurationMs(capcut.timeline_duration_ms)}
          </p>
          <p className="cs-muted">
            Clips listos: {readiness.readyCount}/{readiness.total}
            {readiness.warningCount > 0 && ` · ${readiness.warningCount} advertencia(s)`}
          </p>
          {manifestHint && <p className="cs-muted">{manifestHint}</p>}
        </div>
      )}

      <div className="cs-exp-actions">
        <button type="button" className="cs-btn" disabled={busy} onClick={() => void saveSnapshot()}>
          Guardar snapshot
        </button>
        <button type="button" className="cs-btn cs-btn--ghost" disabled={busy} onClick={() => void downloadCapCut()}>
          Descargar manifest CapCut
        </button>
        <button type="button" className="cs-btn cs-btn--ghost" disabled={busy} onClick={() => void writeCapCutToDisk()}>
          Escribir manifest en servidor
        </button>
      </div>

      {lastWrittenPath && (
        <p className="cs-muted cs-exp-path" title={lastWrittenPath}>
          Manifest guardado: {lastWrittenPath}
        </p>
      )}

      {snapshots.length > 0 && (
        <div className="cs-exp-snapshots">
          <h3>Snapshots editoriales</h3>
          <ul>
            {snapshots.map((s) => (
              <li key={s.snapshot_id}>
                <span>{new Date(s.created_at).toLocaleString()}</span>
                <button
                  type="button"
                  className="cs-btn cs-btn--ghost cs-btn--sm"
                  disabled={busy}
                  onClick={() => {
                    void restoreSnapshot(s.snapshot_id).then(() => onRestored?.());
                  }}
                >
                  Restaurar timeline
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      {capcut && capcut.warnings.length > 0 && (
        <details className="cs-exp-warnings">
          <summary>Advertencias ({capcut.warnings.length})</summary>
          <ul>
            {capcut.warnings.map((w) => (
              <li key={w}>{w}</li>
            ))}
          </ul>
        </details>
      )}
    </section>
  );
}
