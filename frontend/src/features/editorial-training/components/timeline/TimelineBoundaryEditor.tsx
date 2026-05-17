import { memo } from "react";

import type { EditableScene } from "../../types/trainingWorkspace";
import { SceneTimingEditor } from "./SceneTimingEditor";

type Props = {
  scene: EditableScene;
  timelineDuration: number;
  disabled?: boolean;
  validationMessage?: string | null;
  onTimingChange: (start: number, end: number) => void;
  onResetScene: () => void;
};

export const TimelineBoundaryEditor = memo(function TimelineBoundaryEditor({
  scene,
  timelineDuration,
  disabled,
  validationMessage,
  onTimingChange,
  onResetScene,
}: Props) {
  return (
    <section className="et-boundary-editor">
      <div className="et-inline" style={{ justifyContent: "space-between" }}>
        <h4 className="et-boundary-editor__title">Recorte preciso · escena #{scene.scene_index}</h4>
        <button type="button" className="et-btn et-btn--ghost" disabled={disabled} onClick={onResetScene}>
          Reset escena
        </button>
      </div>
      {validationMessage ? <p className="et-error et-error--inline">{validationMessage}</p> : null}
      <SceneTimingEditor
        scene={scene}
        timelineDuration={timelineDuration}
        disabled={disabled}
        onTimingChange={onTimingChange}
      />
    </section>
  );
});
