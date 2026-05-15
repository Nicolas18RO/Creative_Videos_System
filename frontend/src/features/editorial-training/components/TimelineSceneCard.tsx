import type { EditableScene } from "../types/trainingWorkspace";
import { narrativeRoles, visualEnergyToLabel } from "../services/sceneDraftMapper";

type Props = {
  scene: EditableScene;
  disabled?: boolean;
  onPatch: (patch: Partial<EditableScene>) => void;
};

export function TimelineSceneCard({ scene, disabled, onPatch }: Props) {
  const baseRoles = narrativeRoles();
  const roles = baseRoles.includes(scene.narrative_role) ? [...baseRoles] : [scene.narrative_role, ...baseRoles];
  const transitions = ["cut", "dissolve", "whip_pan", "motion_blur", "match_cut"];

  return (
    <article className="et-scene">
      <div className="et-thumb">Vista previa de escena (próximamente)</div>
      <div>
        <div className="et-scene-head">
          <div>
            <strong style={{ color: "#f8fafc" }}>{scene.scene_type_label}</strong>
            <div className="et-muted" style={{ marginTop: 4 }}>
              {scene.time_start.toFixed(2)}s → {scene.time_end.toFixed(2)}s · {scene.duration_seconds.toFixed(2)}s
            </div>
          </div>
          <span className="et-badge">Energía: {scene.energy_label}</span>
        </div>
        <div className="et-row">
          <div className="et-stack">
            <label className="et-label">Rol narrativo</label>
            <select
              className="et-select"
              disabled={disabled}
              value={scene.narrative_role}
              onChange={(e) => onPatch({ narrative_role: e.target.value })}
            >
              {roles.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
          </div>
          <div className="et-stack">
            <label className="et-label">Intensidad emocional (visual)</label>
            <input
              type="range"
              min={0}
              max={1}
              step={0.01}
              disabled={disabled}
              className="et-slider"
              value={scene.visual_energy}
              onChange={(e) => {
                const v = Number(e.target.value);
                onPatch({ visual_energy: v, energy_label: visualEnergyToLabel(v) });
              }}
            />
          </div>
          <div className="et-stack">
            <label className="et-label">Pacing (movimiento)</label>
            <input
              type="range"
              min={0}
              max={1}
              step={0.01}
              disabled={disabled}
              className="et-slider"
              value={scene.motion_intensity}
              onChange={(e) => onPatch({ motion_intensity: Number(e.target.value) })}
            />
          </div>
          <div className="et-stack">
            <label className="et-label">Transición</label>
            <select
              className="et-select"
              disabled={disabled}
              value={scene.transition_type}
              onChange={(e) => onPatch({ transition_type: e.target.value })}
            >
              {transitions.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>
        </div>
        <div className="et-stack" style={{ marginTop: 10 }}>
          <label className="et-label">Tags semánticos (coma)</label>
          <input
            className="et-input"
            disabled={disabled}
            value={scene.semantic_tags.join(", ")}
            onChange={(e) =>
              onPatch({
                semantic_tags: e.target.value
                  .split(",")
                  .map((s) => s.trim().toLowerCase())
                  .filter(Boolean),
              })
            }
          />
        </div>
        <div className="et-stack" style={{ marginTop: 10 }}>
          <label className="et-label">Notas editoriales</label>
          <textarea
            className="et-textarea"
            disabled={disabled}
            style={{ minHeight: 64 }}
            value={scene.editor_notes}
            onChange={(e) => onPatch({ editor_notes: e.target.value })}
          />
        </div>
        <div className="et-inline" style={{ marginTop: 10 }}>
          <button type="button" className="et-btn et-btn--ok" disabled={disabled} onClick={() => onPatch({ editorial_status: "accepted" })}>
            Aceptar escena
          </button>
          <button type="button" className="et-btn et-btn--danger" disabled={disabled} onClick={() => onPatch({ editorial_status: "rejected" })}>
            Rechazar escena
          </button>
          <span className="et-badge">Clip: {scene.clip_id || "—"}</span>
        </div>
      </div>
    </article>
  );
}
