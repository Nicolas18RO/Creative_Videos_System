/** Formato y parseo de tiempos de timeline (sin lógica de negocio editorial). */

const MS_PRECISION = 3;

export function roundSeconds(value: number): number {
  const factor = 10 ** MS_PRECISION;
  return Math.round(value * factor) / factor;
}

export function formatTimelineTime(seconds: number): string {
  const s = roundSeconds(Math.max(0, seconds));
  const mins = Math.floor(s / 60);
  const sec = s - mins * 60;
  const whole = Math.floor(sec);
  const ms = Math.round((sec - whole) * 1000);
  return `${String(mins).padStart(2, "0")}:${String(whole).padStart(2, "0")}.${String(ms).padStart(3, "0")}`;
}

export function parseTimelineTime(input: string): number | null {
  const raw = input.trim();
  if (!raw) return null;
  const parts = raw.split(":");
  if (parts.length === 1) {
    const v = Number(raw);
    return Number.isFinite(v) ? roundSeconds(v) : null;
  }
  if (parts.length === 2) {
    const mins = Number(parts[0]);
    const sec = Number(parts[1]);
    if (!Number.isFinite(mins) || !Number.isFinite(sec)) return null;
    return roundSeconds(mins * 60 + sec);
  }
  if (parts.length === 3) {
    const h = Number(parts[0]);
    const m = Number(parts[1]);
    const s = Number(parts[2]);
    if (![h, m, s].every(Number.isFinite)) return null;
    return roundSeconds(h * 3600 + m * 60 + s);
  }
  return null;
}
