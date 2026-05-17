import { useTimelineDraftStore } from "../../state/timelineDraftStore";

type Props = {
  disabled?: boolean;
  onSave: () => void;
  onValidate: () => void;
};

export function TimelineDraftToolbar({ disabled, onSave, onValidate }: Props) {
  const canUndo = useTimelineDraftStore((s) => s.canUndo());
  const canRedo = useTimelineDraftStore((s) => s.canRedo());
  const hasPending = useTimelineDraftStore((s) => s.hasPendingChanges());
  const saving = useTimelineDraftStore((s) => s.saving);
  const undo = useTimelineDraftStore((s) => s.undo);
  const redo = useTimelineDraftStore((s) => s.redo);
  const resetTimeline = useTimelineDraftStore((s) => s.resetTimeline);

  return (
    <div className="et-draft-toolbar">
      <button type="button" className="et-btn et-btn--ghost" disabled={disabled || !canUndo} onClick={undo}>
        Deshacer
      </button>
      <button type="button" className="et-btn et-btn--ghost" disabled={disabled || !canRedo} onClick={redo}>
        Rehacer
      </button>
      <button type="button" className="et-btn et-btn--ghost" disabled={disabled} onClick={resetTimeline}>
        Reset timeline
      </button>
      <button type="button" className="et-btn et-btn--ghost" disabled={disabled} onClick={onValidate}>
        Validar
      </button>
      <button
        type="button"
        className="et-btn et-btn--primary"
        disabled={disabled || !hasPending || saving}
        onClick={onSave}
      >
        {saving ? "Guardando…" : "Guardar ajustes del timeline"}
      </button>
      {hasPending ? <span className="et-badge et-badge--warn">Cambios sin guardar</span> : null}
    </div>
  );
}
