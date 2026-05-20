import type { EditableScene } from "../../types/trainingWorkspace";
import { clipSourceTaxonomies, emotionalIntents, narrativeIntents } from "../../services/sceneDraftMapper";

type Props = {
  scene: EditableScene;
  disabled?: boolean;
  onPatch: (patch: Partial<EditableScene>) => void;
};

export function SemanticIntentPanel({ scene, disabled, onPatch }: Props) {
  const clipRoles = clipSourceTaxonomies();
  const narrativeRoles = narrativeIntents();
  const emotions = emotionalIntents();

  const clipValue = scene.clip_source_taxonomy || scene.auto_clip_source_taxonomy || "NATURAL";
  const narrativeValue = scene.narrative_intent || scene.narrative_role || "NATURAL";
  const emotionalValue = scene.emotional_intent || scene.auto_emotional_intent || "NEUTRAL";

  return (
    <section className="et-semantic-panel" onClick={(e) => e.stopPropagation()}>
      <p className="et-semantic-panel__title">Capa semántica — clip vs audio</p>

      <div className="et-row">
        <div className="et-stack">
          <label className="et-label">
            Taxonomía del clip (carpeta)
            {scene.has_clip_taxonomy_override ? <span className="et-badge et-badge--override">override</span> : null}
          </label>
          <select
            className="et-select"
            disabled={disabled}
            value={clipValue}
            onChange={(e) => onPatch({ clip_source_taxonomy: e.target.value, human_clip_source_taxonomy: e.target.value })}
          >
            {clipRoles.map((r) => (
              <option key={`clip-${r}`} value={r}>
                {r}
              </option>
            ))}
          </select>
          <span className="et-muted et-hint">Auto: {scene.auto_clip_source_taxonomy || "—"}</span>
        </div>

        <div className="et-stack">
          <label className="et-label">
            Intención narrativa (audio)
            {scene.has_narrative_intent_override ? <span className="et-badge et-badge--override">override</span> : null}
          </label>
          <select
            className="et-select"
            disabled={disabled}
            value={narrativeValue}
            onChange={(e) =>
              onPatch({
                narrative_intent: e.target.value,
                narrative_role: e.target.value,
                human_narrative_intent: e.target.value,
              })
            }
          >
            {narrativeRoles.map((r) => (
              <option key={`nar-${r}`} value={r}>
                {r}
              </option>
            ))}
          </select>
          <span className="et-muted et-hint">Auto audio: {scene.auto_narrative_intent || "—"}</span>
        </div>

        <div className="et-stack">
          <label className="et-label">Intención emocional</label>
          <select
            className="et-select"
            disabled={disabled}
            value={emotionalValue}
            onChange={(e) => onPatch({ emotional_intent: e.target.value, human_emotional_intent: e.target.value })}
          >
            {emotions.map((r) => (
              <option key={`emo-${r}`} value={r}>
                {r}
              </option>
            ))}
          </select>
          <span className="et-muted et-hint">Auto: {scene.auto_emotional_intent || "NEUTRAL"}</span>
        </div>
      </div>

      {scene.visual_style_label ? (
        <p className="et-muted" style={{ marginTop: 8 }}>
          <strong>Estilo visual:</strong> {scene.visual_style_label}
        </p>
      ) : null}
    </section>
  );
}
