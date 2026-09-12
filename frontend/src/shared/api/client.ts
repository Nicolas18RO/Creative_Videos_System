/**
 * Cliente HTTP compartido — solo transporte; sin lógica de dominio ni ranking.
 */

export function apiBase(): string {
  return (import.meta.env.VITE_API_BASE ?? "").replace(/\/$/, "");
}

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly body?: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export async function parseJsonResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text();
    let message = text || res.statusText;
    try {
      const j = JSON.parse(text) as { detail?: unknown };
      if (typeof j.detail === "string") message = j.detail;
      else if (j.detail && typeof j.detail === "object" && "message" in j.detail) {
        message = String((j.detail as { message: unknown }).message);
      }
    } catch {
      /* keep raw text */
    }
    throw new ApiError(message, res.status, text);
  }
  return (await res.json()) as T;
}

export async function apiGet<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${apiBase()}${path}`, { ...init, method: "GET" });
  return parseJsonResponse<T>(res);
}

export async function apiPost<T>(path: string, body: unknown, init?: RequestInit): Promise<T> {
  const res = await fetch(`${apiBase()}${path}`, {
    ...init,
    method: "POST",
    headers: { "Content-Type": "application/json", ...(init?.headers as Record<string, string>) },
    body: JSON.stringify(body),
  });
  return parseJsonResponse<T>(res);
}
