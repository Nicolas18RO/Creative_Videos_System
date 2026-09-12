import { useCallback, useState } from "react";

import { applyOrganize, previewOrganize } from "../api/studioOrganizeApi";
import { canApplyOrganization } from "../presentation/organizationPresentation";
import type { ClipSummaryDto, OrganizeResultDto } from "../../types/studio";

export function useClipOrganization() {
  const [proposal, setProposal] = useState<OrganizeResultDto | null>(null);
  const [confirmed, setConfirmed] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const reset = useCallback(() => {
    setProposal(null);
    setConfirmed(false);
    setError(null);
  }, []);

  const preview = useCallback(async (clip: ClipSummaryDto) => {
    setBusy(true);
    setError(null);
    setConfirmed(false);
    try {
      const result = await previewOrganize(clip.clip_id);
      setProposal(result);
    } catch (e) {
      setProposal(null);
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }, []);

  const apply = useCallback(
    async (clip: ClipSummaryDto) => {
      if (!canApplyOrganization(proposal, { confirmed, busy })) {
        setError("Confirma la propuesta antes de aplicar. El preview no mueve archivos.");
        return null;
      }
      setBusy(true);
      setError(null);
      try {
        const result = await applyOrganize(clip.clip_id);
        setProposal(result);
        if (result.risk === "COLLISION") {
          setError("Colisión: no se movió el archivo.");
        }
        return result;
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
        return null;
      } finally {
        setBusy(false);
      }
    },
    [busy, confirmed, proposal],
  );

  return {
    proposal,
    confirmed,
    setConfirmed,
    busy,
    error,
    preview,
    apply,
    reset,
    canApply: canApplyOrganization(proposal, { confirmed, busy }),
  };
}
