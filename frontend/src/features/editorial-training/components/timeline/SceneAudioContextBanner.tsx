import { memo } from "react";

import type { EditableScene } from "../../types/trainingWorkspace";
import {
  sceneAudioContextText,
  sceneAudioTimeRangeLabel,
  sceneHasAudioContext,
} from "../../services/sceneAudioContext";

type Props = {
  scene: EditableScene;
  compact?: boolean;
};

export const SceneAudioContextBanner = memo(function SceneAudioContextBanner({ scene, compact }: Props) {
  const text = sceneAudioContextText(scene);
  const hasText = sceneHasAudioContext(scene);
  const timeLabel = sceneAudioTimeRangeLabel(scene);
  const emotional = scene.emotional_intent || scene.auto_emotional_intent;

  return (
    <aside
      className={`et-audio-context ${compact ? "et-audio-context--compact" : ""} ${hasText ? "" : "et-audio-context--empty"}`}
      aria-label="Contexto de audio de la escena"
      onClick={(e) => e.stopPropagation()}
    >
      <header className="et-audio-context__head">
        <span className="et-audio-context__kicker">Audio en este clip</span>
        <span className="et-audio-context__time et-mono" title="Ventana temporal en el creativo">
          {timeLabel}
        </span>
      </header>

      {hasText ? (
        <p className="et-audio-context__quote" lang="es">
          «{text}»
        </p>
      ) : (
        <p className="et-audio-context__empty">
          Sin transcripción para esta escena. Ejecuta el análisis de audio para alinear clip y guion.
        </p>
      )}

      <footer className="et-audio-context__meta">
        {emotional ? <span className="et-badge et-badge--emotion">{emotional}</span> : null}
        {scene.visual_style_label ? (
          <span className="et-muted et-audio-context__visual">{scene.visual_style_label}</span>
        ) : null}
      </footer>
    </aside>
  );
});
