import { useTrainingWorkspaceStore } from "../state/trainingWorkspaceStore";
import { useEditorialReview } from "../hooks/useEditorialReview";

type Props = { disabled?: boolean };

export function TimelineReviewToolbar({ disabled }: Props) {
  const selected = useTrainingWorkspaceStore((s) => s.selectedSceneIndices);
  const { bulkReview } = useEditorialReview();

  return (
    <div className="vt-review-toolbar">
      <span className="et-muted">{selected.length} seleccionada(s)</span>
      <button type="button" className="et-btn et-btn--ok" disabled={disabled || !selected.length} onClick={() => void bulkReview(selected, "accepted")}>
        Aceptar selección
      </button>
      <button type="button" className="et-btn et-btn--danger" disabled={disabled || !selected.length} onClick={() => void bulkReview(selected, "rejected")}>
        Rechazar selección
      </button>
      <button type="button" className="et-btn et-btn--ghost" disabled={disabled} onClick={() => useTrainingWorkspaceStore.getState().clearSelection()}>
        Limpiar selección
      </button>
    </div>
  );
}
