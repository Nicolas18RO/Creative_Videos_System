import { useStudioStore } from "../state/studioStore";

export function ApiHealthBanner() {
  const healthOk = useStudioStore((s) => s.healthOk);
  const busy = useStudioStore((s) => s.busy);

  if (healthOk === null || busy) return null;
  if (healthOk) {
    return (
      <div className="cs-banner cs-banner--ok" role="status">
        API lista para análisis y retrieval
      </div>
    );
  }
  return (
    <div className="cs-banner cs-banner--warn" role="alert">
      La API reporta dependencias incompletas. Revisa <code>GET /analyze/health</code> antes de analizar audio.
    </div>
  );
}
