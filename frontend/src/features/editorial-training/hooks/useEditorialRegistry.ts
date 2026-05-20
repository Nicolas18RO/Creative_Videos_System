import { useCallback, useEffect, useState } from "react";

import { checkRegistryDuplicates, fetchRegistrySessions } from "../api/editorialRegistryApi";
import type { EditorialRegistrySessionDto, EditorialRegistrySummaryDto, RegistryStatusFilter } from "../types/editorialRegistry";

export function useEditorialRegistry() {
  const [sessions, setSessions] = useState<EditorialRegistrySessionDto[]>([]);
  const [summary, setSummary] = useState<EditorialRegistrySummaryDto | null>(null);
  const [statusFilter, setStatusFilter] = useState<RegistryStatusFilter>("all");
  const [productFilter, setProductFilter] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchRegistrySessions({
        status: statusFilter === "all" ? undefined : statusFilter,
        product_category: productFilter.trim() || undefined,
      });
      setSessions(data.sessions);
      setSummary(data.summary);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }, [productFilter, statusFilter]);

  useEffect(() => {
    void reload();
  }, [reload]);

  const checkDuplicates = useCallback(async (creativeId: string, creativeLabel: string) => {
    try {
      return await checkRegistryDuplicates(creativeId, creativeLabel);
    } catch {
      return [];
    }
  }, []);

  return {
    sessions,
    summary,
    statusFilter,
    setStatusFilter,
    productFilter,
    setProductFilter,
    loading,
    error,
    reload,
    checkDuplicates,
  };
}
