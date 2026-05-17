import type { ReviewStatus } from "../types/trainingWorkspace";

const LABELS: Record<ReviewStatus, string> = {
  pending: "Pendiente",
  accepted: "Aceptada",
  rejected: "Rechazada",
  merged: "Fusionada",
  edited: "Editada",
};

type Props = { status: ReviewStatus };

export function ReviewStatusBadge({ status }: Props) {
  return <span className={`et-review-badge et-review-badge--${status}`}>{LABELS[status] ?? status}</span>;
}
