type Props = {
  disabled?: boolean;
  onCommit: () => Promise<void>;
};

export function CommitTrainingPanel({ disabled, onCommit }: Props) {
  return (
    <section className="et-card">
      <h2>Paso 7 — Commit de aprendizaje</h2>
      <p className="et-muted" style={{ marginBottom: 14 }}>
        Confirma el timeline revisado y las correcciones. AICOS persistirá el dataset editorial, actualizará embeddings de estilo si
        procede e ingerirá señales de refuerzo humano.
      </p>
      <button type="button" className="et-btn et-btn--primary" disabled={disabled} onClick={() => void onCommit()}>
        Entrenar AICOS con este creativo
      </button>
    </section>
  );
}
