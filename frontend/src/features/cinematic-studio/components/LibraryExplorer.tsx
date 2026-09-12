import type { ClipSummaryDto } from "../types/studio";

type Props = {
  stats: { total_clips: number; naming_compliant: number } | null;
  clips: ClipSummaryDto[];
  loaded: number;
  total: number;
  searchQuery: string;
  onSearchQueryChange: (q: string) => void;
  onSearch: () => void;
  onLoadMore: () => void;
  onActivateClip: (clip: ClipSummaryDto) => void;
  busy: boolean;
};

export function LibraryExplorer({
  stats,
  clips,
  loaded,
  total,
  searchQuery,
  onSearchQueryChange,
  onSearch,
  onLoadMore,
  onActivateClip,
  busy,
}: Props) {
  return (
    <aside className="cs-library">
      <div className="cs-library__stats">
        <h2>Biblioteca</h2>
        {stats ? (
          <p>
            Clips: <strong>{stats.total_clips}</strong> · Naming OK:{" "}
            <strong>{stats.naming_compliant}</strong>
          </p>
        ) : (
          <p className="cs-muted">Cargando stats…</p>
        )}
      </div>
      <div className="cs-library__search">
        <input
          type="search"
          className="cs-input"
          placeholder="Ej: dolor de rodilla escaleras…"
          value={searchQuery}
          onChange={(e) => onSearchQueryChange(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && onSearch()}
        />
        <button type="button" className="cs-btn" disabled={busy} onClick={onSearch}>
          Buscar
        </button>
      </div>
      <p className="cs-library__status">
        Mostrando {loaded} / {total}
      </p>
      <ul className="cs-library__list">
        {clips.map((c) => {
          const dur =
            typeof c.duration_ms === "number" ? `${Math.floor(c.duration_ms / 1000)}s` : "—";
          return (
            <li key={c.clip_id}>
              <button
                type="button"
                className="cs-library__clip-btn"
                onClick={() => onActivateClip(c)}
                title={c.relative_path}
              >
                {c.name} ({dur})
              </button>
            </li>
          );
        })}
      </ul>
      {loaded < total && (
        <button type="button" className="cs-btn cs-btn--ghost" disabled={busy} onClick={onLoadMore}>
          Cargar más
        </button>
      )}
    </aside>
  );
}
