import { memo } from "react";

import { useEditorialRegistry } from "../../hooks/useEditorialRegistry";
import type { EditorialRegistrySessionDto, RegistryStatusFilter } from "../../types/editorialRegistry";
import { RegistrySessionRow } from "./RegistrySessionRow";
import { RegistrySummaryBar } from "./RegistrySummaryBar";

type Props = {
  onOpenSession?: (sessionId: string) => void;
};

const FILTERS: { id: RegistryStatusFilter; label: string }[] = [
  { id: "all", label: "Todas" },
  { id: "committed", label: "En dataset" },
  { id: "awaiting_human", label: "Revisión" },
  { id: "analyzing", label: "Analizando" },
  { id: "failed", label: "Fallidas" },
];

export function DatasetSessionsRegistry({ onOpenSession }: Props) {
  const {
    sessions,
    summary,
    statusFilter,
    setStatusFilter,
    productFilter,
    setProductFilter,
    loading,
    error,
    reload,
  } = useEditorialRegistry();

  const committed = sessions.filter((s) => s.status === "committed");
  const others = sessions.filter((s) => s.status !== "committed");

  return (
    <section className="et-registry">
      <header className="et-registry__head">
        <div>
          <h2>Dataset Sessions Registry</h2>
          <p className="et-muted">
            Creativos ya procesados o en curso. Evita subir duplicados revisando sesiones committeadas.
          </p>
        </div>
        <button type="button" className="et-btn et-btn--ghost" disabled={loading} onClick={() => void reload()}>
          Actualizar
        </button>
      </header>

      {summary ? <RegistrySummaryBar summary={summary} /> : null}

      <div className="et-registry__filters">
        {FILTERS.map((f) => (
          <button
            key={f.id}
            type="button"
            className={`et-step-pill ${statusFilter === f.id ? "et-step-pill--active" : ""}`}
            onClick={() => setStatusFilter(f.id)}
          >
            {f.label}
          </button>
        ))}
        <input
          className="et-input et-registry__search"
          placeholder="Filtrar categoría producto…"
          value={productFilter}
          onChange={(e) => setProductFilter(e.target.value)}
        />
      </div>

      {error ? <div className="et-error">{error}</div> : null}
      {loading ? <p className="et-muted">Cargando registro…</p> : null}

      {!loading && statusFilter !== "committed" && committed.length > 0 && statusFilter === "all" ? (
        <RegistryGroup title="En dataset (committed)" sessions={committed} onOpenSession={onOpenSession} />
      ) : null}

      {!loading && (statusFilter === "committed" ? committed : others).length > 0 ? (
        <RegistryGroup
          title={statusFilter === "committed" ? "En dataset" : "Otras sesiones"}
          sessions={statusFilter === "committed" ? committed : statusFilter === "all" ? others : sessions}
          onOpenSession={onOpenSession}
        />
      ) : null}

      {!loading && !sessions.length ? (
        <p className="et-muted et-registry__empty">No hay sesiones que coincidan con el filtro.</p>
      ) : null}
    </section>
  );
}

const RegistryGroup = memo(function RegistryGroup({
  title,
  sessions,
  onOpenSession,
}: {
  title: string;
  sessions: EditorialRegistrySessionDto[];
  onOpenSession?: (sessionId: string) => void;
}) {
  return (
    <div className="et-registry__group">
      <h3 className="et-registry__group-title">{title}</h3>
      <div className="et-registry__list">
        {sessions.map((s) => (
          <RegistrySessionRow key={s.session_id} session={s} onOpen={onOpenSession} />
        ))}
      </div>
    </div>
  );
});
