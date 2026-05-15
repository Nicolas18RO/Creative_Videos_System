type Props = {
  label: string;
  filename?: string;
  sizeBytes?: number;
  durationMs?: number | null;
  progress: number;
};

function fmtBytes(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / (1024 * 1024)).toFixed(2)} MB`;
}

function fmtMs(ms: number | null | undefined): string {
  if (ms == null || ms <= 0) return "—";
  const s = Math.round(ms / 1000);
  const m = Math.floor(s / 60);
  const r = s % 60;
  return `${m}:${r.toString().padStart(2, "0")}`;
}

export function UploadProgressCard({ label, filename, sizeBytes, durationMs, progress }: Props) {
  return (
    <div className="et-card" style={{ marginBottom: 0 }}>
      <h2 style={{ fontSize: "1rem" }}>{label}</h2>
      {filename ? (
        <div className="et-stack" style={{ marginTop: 8 }}>
          <span className="et-badge">{filename}</span>
          {sizeBytes != null ? <span className="et-muted">Tamaño: {fmtBytes(sizeBytes)}</span> : null}
          <span className="et-muted">Duración (ffprobe): {fmtMs(durationMs ?? null)}</span>
        </div>
      ) : (
        <p className="et-muted" style={{ marginTop: 8 }}>
          Aún sin archivo
        </p>
      )}
      {progress > 0 && progress < 1 ? (
        <div className="et-loader" style={{ marginTop: 12 }}>
          <div className="et-loader-bar">
            <span />
          </div>
          <span className="et-muted">Subiendo…</span>
        </div>
      ) : null}
    </div>
  );
}
