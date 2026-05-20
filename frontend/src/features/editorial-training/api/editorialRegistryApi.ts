import type {
  EditorialRegistryListDto,
  EditorialRegistrySessionDto,
  EditorialRegistrySummaryDto,
} from "../types/editorialRegistry";

const apiBase = () => (import.meta.env.VITE_API_BASE ?? "").replace(/\/$/, "") || "";

async function parseJson<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  return (await res.json()) as T;
}

export async function fetchRegistrySessions(params?: {
  status?: string;
  product_category?: string;
}): Promise<EditorialRegistryListDto> {
  const q = new URLSearchParams();
  if (params?.status && params.status !== "all") q.set("status", params.status);
  if (params?.product_category) q.set("product_category", params.product_category);
  const qs = q.toString();
  const res = await fetch(`${apiBase()}/editorial-registry/sessions${qs ? `?${qs}` : ""}`);
  return parseJson(res);
}

export async function fetchRegistrySummary(): Promise<EditorialRegistrySummaryDto> {
  const res = await fetch(`${apiBase()}/editorial-registry/summary`);
  return parseJson(res);
}

export async function checkRegistryDuplicates(
  creativeId: string,
  creativeLabel: string,
): Promise<EditorialRegistrySessionDto[]> {
  const q = new URLSearchParams();
  if (creativeId) q.set("creative_id", creativeId);
  if (creativeLabel) q.set("creative_label", creativeLabel);
  const res = await fetch(`${apiBase()}/editorial-registry/duplicates-check?${q.toString()}`);
  const body = await parseJson<{ possible_duplicates: EditorialRegistrySessionDto[] }>(res);
  return body.possible_duplicates ?? [];
}
