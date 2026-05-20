import type { EditorialRegistrySummaryDto } from "../../types/editorialRegistry";

type Props = { summary: EditorialRegistrySummaryDto };

export function RegistrySummaryBar({ summary }: Props) {
  return (
    <div className="et-registry-kpis">
      <div className="et-kpi et-kpi--committed">
        <span>En dataset</span>
        <strong>{summary.committed}</strong>
      </div>
      <div className="et-kpi">
        <span>En revisión</span>
        <strong>{summary.awaiting_human}</strong>
      </div>
      <div className="et-kpi">
        <span>Total</span>
        <strong>{summary.total}</strong>
      </div>
      <div className="et-kpi">
        <span>Con timeline</span>
        <strong>{summary.with_timeline}</strong>
      </div>
      <div className="et-kpi">
        <span>Con feedback</span>
        <strong>{summary.with_feedback}</strong>
      </div>
    </div>
  );
}
