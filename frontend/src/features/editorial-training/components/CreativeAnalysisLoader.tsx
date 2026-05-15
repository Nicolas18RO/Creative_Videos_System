const STAGES = [
  "Extrayendo escenas…",
  "Detectando hooks…",
  "Midiendo pacing…",
  "Capturando ritmo editorial…",
  "Generando embeddings de estilo…",
  "Análisis completo",
];

type Props = {
  active: boolean;
  stageIndex: number;
};

export function CreativeAnalysisLoader({ active, stageIndex }: Props) {
  if (!active) return null;
  const idx = Math.min(Math.max(stageIndex, 0), STAGES.length - 1);
  return (
    <div className="et-card">
      <h2>Analizando creativo…</h2>
      <p className="et-muted" style={{ marginBottom: 12 }}>
        AICOS está transcribiendo, segmentando y construyendo el timeline editorial. Puede tardar varios minutos en CPU.
      </p>
      <div className="et-loader-bar" style={{ marginBottom: 10 }}>
        <span />
      </div>
      <p style={{ margin: 0, color: "#bae6fd", fontWeight: 600 }}>{STAGES[idx]}</p>
    </div>
  );
}
