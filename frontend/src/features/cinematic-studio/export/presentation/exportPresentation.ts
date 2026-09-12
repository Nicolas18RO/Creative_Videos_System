import type { CapCutManifestDto, ExportManifestDto } from "../types/export";

export function capcutReadinessSummary(manifest: CapCutManifestDto): {
  readyCount: number;
  total: number;
  warningCount: number;
} {
  const total = manifest.entries.length;
  const readyCount = manifest.entries.filter((e) => e.clip_exists && e.clip_id).length;
  return { readyCount, total, warningCount: manifest.warnings.length };
}

export function exportManifestSummary(manifest: ExportManifestDto): string {
  const missing = manifest.missing_assets.length;
  if (missing === 0) return "Todos los clips listos para export.";
  return `${missing} advertencia(s) de assets.`;
}

export function formatDurationMs(ms: number): string {
  const sec = Math.floor(ms / 1000);
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  return `${m}:${s.toString().padStart(2, "0")}`;
}
