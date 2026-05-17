const MAP: Record<string, string> = {
  HOOK: "#f43f5e",
  PROBLEM: "#f97316",
  BENEFIT: "#22c55e",
  RESULT: "#14b8a6",
  AUTHORITY: "#6366f1",
  SOCIAL_PROOF: "#a855f7",
  NATURAL: "#64748b",
  CTA: "#eab308",
};

export function narrativeColor(role: string): string {
  const k = (role || "NATURAL").trim().toUpperCase();
  return MAP[k] ?? "#38bdf8";
}
