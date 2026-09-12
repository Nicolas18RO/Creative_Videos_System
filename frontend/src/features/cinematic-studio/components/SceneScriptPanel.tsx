import { mapSceneDetail } from "../presentation/studioScenePresentation";
import type { ClipSummaryDto, SceneDetailDto } from "../types/studio";

type Props = {
  scene: SceneDetailDto | null;
  inspectedClip: ClipSummaryDto | null;
};

export function SceneScriptPanel({ scene, inspectedClip }: Props) {
  if (inspectedClip) {
    const dur =
      typeof inspectedClip.duration_ms === "number"
        ? `${Math.floor(inspectedClip.duration_ms / 1000)} s`
        : "—";
    return (
      <section className="cs-panel cs-script-panel">
        <h2>Biblioteca</h2>
        <p className="cs-script-panel__meta">
          <strong>{inspectedClip.name}</strong>
          <br />
          Función: {inspectedClip.narrative_function ?? "—"} · Sub: {inspectedClip.subcategory ?? "—"}
          <br />
          Duración: {dur}
        </p>
        <p className="cs-script-panel__path">{inspectedClip.relative_path || "—"}</p>
        <div className="cs-script-panel__body">
          <h3>Texto semántico</h3>
          <p>{inspectedClip.semantic_excerpt || "—"}</p>
        </div>
      </section>
    );
  }

  if (!scene) {
    return (
      <section className="cs-panel cs-script-panel">
        <h2>Guion / escena</h2>
        <p className="cs-muted">Selecciona una escena del proyecto.</p>
      </section>
    );
  }

  const v = mapSceneDetail(scene);
  return (
    <section className="cs-panel cs-script-panel">
      <h2>Guion / escena</h2>
      <p className="cs-script-panel__meta">
        Escena #{v.sceneIndex} · {v.narrativeFunction} · Hook: {v.isHook ? "Sí" : "No"} · Género:{" "}
        {v.genderHint}
      </p>
      <div className="cs-script-panel__body">
        <h3>Concepto</h3>
        <p>{v.concept || "—"}</p>
        <h3>Texto</h3>
        <p>{v.text || "—"}</p>
      </div>
    </section>
  );
}
