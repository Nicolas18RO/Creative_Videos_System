import type { GapDto } from "../types/studio";

type Props = {
  gap: GapDto | null;
  explorationHint: string | null;
};

export function SceneGapPanel({ gap, explorationHint }: Props) {
  return (
    <section className="cs-panel cs-gap-panel">
      <h2>Gaps (M3)</h2>
      {explorationHint && <p className="cs-gap-panel__hint">{explorationHint}</p>}
      {!explorationHint && !gap && (
        <p className="cs-muted">Sin gap registrado para esta escena.</p>
      )}
      {gap && (
        <div className="cs-gap-panel__body">
          <p>
            <strong>Tipo</strong>: {gap.gap_type}
          </p>
          <p>
            <strong>Keywords TikTok</strong>
            <br />
            {gap.tiktok_keywords?.length ? gap.tiktok_keywords.join(", ") : "—"}
          </p>
          <p>
            <strong>Prompt imagen</strong>
            <br />
            {gap.ai_image_prompt || "—"}
          </p>
          <p>
            <strong>Prompt movimiento</strong>
            <br />
            {gap.ai_motion_prompt || "—"}
          </p>
          <p>
            <strong>Taxonomía sugerida</strong>
            <br />
            {gap.taxonomy_suggestion || "—"}
          </p>
        </div>
      )}
    </section>
  );
}
