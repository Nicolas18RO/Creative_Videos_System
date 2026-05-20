import { memo } from "react";

import type { EditorialRegistrySessionDto } from "../../types/editorialRegistry";

const STATUS_LABEL: Record<string, string> = {
  committed: "En dataset",
  awaiting_human: "Revisión humana",
  analyzing: "Analizando",
  failed: "Fallida",
  draft: "Borrador",
  ready: "Lista",
};

type Props = {
  session: EditorialRegistrySessionDto;
  onOpen?: (sessionId: string) => void;
};

function formatDate(iso: string | null): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

export const RegistrySessionRow = memo(function RegistrySessionRow({ session, onOpen }: Props) {
  const label = session.creative_label || session.creative_id || session.session_id;
  const statusClass = `et-registry-row et-registry-row--${session.status}`;

  return (
    <article className={statusClass}>
      <div className="et-registry-row__main">
        <strong>{label}</strong>
        <span className={`et-registry-status et-registry-status--${session.status}`}>
          {STATUS_LABEL[session.status] ?? session.status}
        </span>
      </div>
      <div className="et-registry-row__meta">
        <span>{session.project_label || "—"}</span>
        <span>·</span>
        <span>{session.product_category || "—"}</span>
        <span>·</span>
        <span>{session.scene_count} escenas</span>
        <span>·</span>
        <span>{session.duration_seconds.toFixed(1)}s</span>
      </div>
      <div className="et-registry-row__dates et-muted">
        Creada: {formatDate(session.created_at)}
        {session.committed_at ? <> · Commit: {formatDate(session.committed_at)}</> : null}
      </div>
      <div className="et-registry-row__flags">
        {session.has_timeline ? <span className="et-badge">Timeline</span> : null}
        {session.has_feedback ? <span className="et-badge">Feedback</span> : null}
        {session.notes ? <span className="et-badge et-badge--notes" title={session.notes}>Notas</span> : null}
      </div>
      {onOpen ? (
        <button type="button" className="et-btn et-btn--ghost et-registry-row__open" onClick={() => onOpen(session.session_id)}>
          Abrir sesión
        </button>
      ) : null}
    </article>
  );
});
