import { useTrainingWorkspaceStore } from "../state/trainingWorkspaceStore";
import { TimelineSceneCard } from "./TimelineSceneCard";

export function TimelineWorkspace() {
  const scenes = useTrainingWorkspaceStore((s) => s.sceneDrafts);
  const patchScene = useTrainingWorkspaceStore((s) => s.patchScene);
  const loading = useTrainingWorkspaceStore((s) => s.loading);

  if (!scenes.length) {
    return (
      <section className="et-card">
        <h2>Paso 4 — Línea de tiempo cinematográfica</h2>
        <p className="et-muted">Cuando el análisis termine, las escenas aparecerán aquí listas para revisión humana.</p>
      </section>
    );
  }

  return (
    <section className="et-card">
      <h2>Paso 4 — Línea de tiempo cinematográfica</h2>
      <p className="et-muted" style={{ marginBottom: 14 }}>
        Corrige roles, energía, pacing y transiciones sin tocar JSON. Guarda los cambios antes de registrar señales de refuerzo.
      </p>
      <div className="et-scene-grid">
        {scenes.map((s) => (
          <TimelineSceneCard key={s.scene_index} scene={s} disabled={loading} onPatch={(p) => patchScene(s.scene_index, p)} />
        ))}
      </div>
    </section>
  );
}
