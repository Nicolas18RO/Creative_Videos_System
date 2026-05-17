import { useTrainingWorkspaceStore } from "../state/trainingWorkspaceStore";

type Props = {
  onConfirm: () => void;
  onCancel: () => void;
  busy?: boolean;
};

export function MergeConfirmModal({ onConfirm, onCancel, busy }: Props) {
  const preview = useTrainingWorkspaceStore((s) => s.mergePreview);
  const scenes = useTrainingWorkspaceStore((s) => s.sceneDrafts);
  if (!preview) return null;

  const a = scenes.find((s) => s.scene_index === preview.a);
  const b = scenes.find((s) => s.scene_index === preview.b);
  if (!a || !b) return null;

  const start = Math.min(a.time_start, b.time_start);
  const end = Math.max(a.time_end, b.time_end);

  return (
    <div className="et-modal-backdrop" role="dialog" aria-modal="true">
      <div className="et-modal">
        <h3>Fusionar escenas</h3>
        <p className="et-muted">
          #{a.scene_index} ({a.time_start.toFixed(1)}s–{a.time_end.toFixed(1)}s) + #{b.scene_index} (
          {b.time_start.toFixed(1)}s–{b.time_end.toFixed(1)}s)
        </p>
        <p className="et-muted">Resultado estimado: {start.toFixed(1)}s → {end.toFixed(1)}s · {(end - start).toFixed(1)}s</p>
        <p className="et-muted">Las escenas originales se conservan como fusionadas (auditoría).</p>
        <div className="et-inline" style={{ marginTop: 14 }}>
          <button type="button" className="et-btn et-btn--primary" disabled={busy} onClick={onConfirm}>
            Confirmar fusión
          </button>
          <button type="button" className="et-btn et-btn--ghost" disabled={busy} onClick={onCancel}>
            Cancelar
          </button>
        </div>
      </div>
    </div>
  );
}
