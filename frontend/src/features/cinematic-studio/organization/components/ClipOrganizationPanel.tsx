import { useEffect } from "react";

import type { ClipSummaryDto } from "../../types/studio";
import { useClipOrganization } from "../hooks/useClipOrganization";
import {
  currentLocation,
  proposedLocation,
  riskLabel,
} from "../presentation/organizationPresentation";

type Props = {
  clip: ClipSummaryDto | null;
  onApplied?: () => void;
};

export function ClipOrganizationPanel({ clip, onApplied }: Props) {
  const { proposal, confirmed, setConfirmed, busy, error, preview, apply, reset, canApply } =
    useClipOrganization();

  useEffect(() => {
    reset();
  }, [clip?.clip_id, reset]);

  if (!clip) {
    return (
      <section className="cs-card cs-org-panel">
        <h2>Organización M4</h2>
        <p className="cs-muted">Selecciona un clip de la biblioteca para calcular una propuesta.</p>
      </section>
    );
  }

  const collision = proposal?.risk === "COLLISION";

  return (
    <section className="cs-card cs-org-panel" data-testid="clip-organization-panel">
      <header className="cs-org-panel__head">
        <h2>Organización M4</h2>
        <span className="cs-muted">Preview primero · apply solo con confirmación</span>
      </header>

      <p className="cs-org-row">
        <span className="cs-muted">Ubicación actual</span>
        <strong data-testid="org-current">{currentLocation(clip)}</strong>
      </p>

      {proposal && (
        <>
          <p className="cs-org-row">
            <span className="cs-muted">Destino propuesto</span>
            <strong data-testid="org-destination">{proposedLocation(proposal)}</strong>
          </p>
          <p className="cs-org-row">
            <span className="cs-muted">Nombre propuesto</span>
            <strong data-testid="org-filename">{proposal.proposed_filename || "—"}</strong>
          </p>
          <p className="cs-org-row">
            <span className="cs-muted">Acción / riesgo</span>
            <strong data-testid="org-risk">
              {proposal.action || "—"} · {riskLabel(proposal.risk)}
            </strong>
          </p>
          {proposal.message && <p className="cs-muted">{proposal.message}</p>}
          {collision && (
            <p className="cs-banner cs-banner--warn" role="alert" data-testid="org-collision">
              Colisión: no se aplicará el move.
            </p>
          )}
          {proposal.applied && (
            <p className="cs-banner cs-banner--ok" data-testid="org-applied">
              Archivo organizado.
            </p>
          )}
        </>
      )}

      {error && (
        <p className="cs-banner cs-banner--warn" role="alert" data-testid="org-error">
          {error}
        </p>
      )}

      <div className="cs-org-actions">
        <button
          type="button"
          className="cs-btn"
          disabled={busy}
          data-testid="org-preview"
          onClick={() => void preview(clip)}
        >
          Calcular propuesta
        </button>
        <label className="cs-org-confirm">
          <input
            type="checkbox"
            checked={confirmed}
            disabled={!proposal || busy || collision}
            data-testid="org-confirm"
            onChange={(e) => setConfirmed(e.target.checked)}
          />
          Confirmo el move / rename
        </label>
        <button
          type="button"
          className="cs-btn"
          disabled={!canApply}
          data-testid="org-apply"
          onClick={async () => {
            const result = await apply(clip);
            if (result?.applied) onApplied?.();
          }}
        >
          Aplicar organización
        </button>
      </div>
    </section>
  );
}
