import type { ClipSummaryDto, OrganizeResultDto } from "../../types/studio";

export function canApplyOrganization(
  proposal: OrganizeResultDto | null,
  opts: { confirmed: boolean; busy: boolean },
): boolean {
  if (!proposal || opts.busy || !opts.confirmed) return false;
  if (proposal.risk === "COLLISION") return false;
  return proposal.eligible === true && proposal.risk === "NONE";
}

export function riskLabel(risk: string | null | undefined): string {
  switch (risk) {
    case "NONE":
      return "Sin riesgo";
    case "COLLISION":
      return "Colisión: el destino ya existe";
    case "INVALID":
      return "Propuesta inválida";
    case "UNSAFE":
      return "Ruta insegura";
    case "INVALID_TAXONOMY":
      return "Taxonomía inválida";
    default:
      return risk || "—";
  }
}

export function currentLocation(clip: ClipSummaryDto): string {
  return clip.relative_path || clip.name || "—";
}

export function proposedLocation(proposal: OrganizeResultDto | null): string {
  if (!proposal) return "—";
  return proposal.destination_path || "—";
}
