import { useEffect, useState } from "react";

import type { CorrectionItemPayload } from "../api/editorialTrainingApi";
import { useTrainingWorkspaceStore } from "../state/trainingWorkspaceStore";

type Props = {
  disabled?: boolean;
  onSend: (items: CorrectionItemPayload[]) => Promise<void>;
};

export function HumanCorrectionPanel({ disabled, onSend }: Props) {
  const scenes = useTrainingWorkspaceStore((s) => s.sceneDrafts);
  const [idx, setIdx] = useState(0);
  const scene = scenes[idx];

  useEffect(() => {
    if (idx >= scenes.length) setIdx(0);
  }, [idx, scenes.length]);

  if (!scenes.length) {
    return (
      <section className="et-card">
        <h2>Paso 5 — Correcciones humanas</h2>
        <p className="et-muted">Selecciona escenas en el paso 4 para habilitar refuerzo editorial.</p>
      </section>
    );
  }

  return (
    <section className="et-card">
      <h2>Paso 5 — Correcciones humanas</h2>
      <p className="et-muted" style={{ marginBottom: 12 }}>
        Envía señales de refuerzo (6.6) con recompensas claras. La edición fina de timing sigue en las tarjetas del paso 4.
      </p>
      <div className="et-stack">
        <label className="et-label">Escena</label>
        <select
          className="et-select"
          value={scene?.scene_index ?? scenes[0].scene_index}
          onChange={(e) => {
            const v = Number(e.target.value);
            const i = scenes.findIndex((s) => s.scene_index === v);
            setIdx(i >= 0 ? i : 0);
          }}
          disabled={disabled}
        >
          {scenes.map((s) => (
            <option key={s.scene_index} value={s.scene_index}>
              #{s.scene_index} · {s.scene_type_label}
            </option>
          ))}
        </select>
      </div>
      {scene ? (
        <div className="et-inline" style={{ marginTop: 14, gap: 10 }}>
          <button
            type="button"
            className="et-btn et-btn--ok"
            disabled={disabled}
            onClick={() =>
              void onSend([
                {
                  event_kind: "clip_accept",
                  reward: 1,
                  clip_id: scene.clip_id || null,
                  scene_index: scene.scene_index,
                  narrative_function: scene.narrative_role,
                  transition_type: scene.transition_type,
                },
              ])
            }
          >
            Registrar aceptación
          </button>
          <button
            type="button"
            className="et-btn et-btn--danger"
            disabled={disabled}
            onClick={() =>
              void onSend([
                {
                  event_kind: "clip_reject",
                  reward: -0.6,
                  clip_id: scene.clip_id || null,
                  scene_index: scene.scene_index,
                  narrative_function: scene.narrative_role,
                  transition_type: scene.transition_type,
                },
              ])
            }
          >
            Registrar rechazo
          </button>
        </div>
      ) : null}
    </section>
  );
}
