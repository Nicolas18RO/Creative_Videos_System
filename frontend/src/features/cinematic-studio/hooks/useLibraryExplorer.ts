import { useCallback } from "react";

import { postSearch } from "../api/studioSearchApi";
import { listLibraryClips } from "../api/studioLibraryApi";
import { useStudioStore } from "../state/studioStore";
import type { ClipSummaryDto } from "../types/studio";

export function useLibraryExplorer() {
  const appendLibraryClips = useStudioStore((s) => s.appendLibraryClips);
  const setLibraryPage = useStudioStore((s) => s.setLibraryPage);
  const resetLibraryList = useStudioStore((s) => s.resetLibraryList);
  const libraryPageSize = useStudioStore((s) => s.libraryPageSize);
  const libraryLoaded = useStudioStore((s) => s.libraryLoaded);
  const libraryTotal = useStudioStore((s) => s.libraryTotal);
  const setInspectedLibraryClip = useStudioStore((s) => s.setInspectedLibraryClip);
  const setLibraryExploreCandidates = useStudioStore((s) => s.setLibraryExploreCandidates);
  const setBusy = useStudioStore((s) => s.setBusy);
  const setError = useStudioStore((s) => s.setError);

  const loadMore = useCallback(async () => {
    if (libraryLoaded >= libraryTotal) return;
    setBusy(true);
    try {
      const page = await listLibraryClips(libraryPageSize, libraryLoaded);
      appendLibraryClips(page.items, page.offset + page.items.length);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }, [appendLibraryClips, libraryLoaded, libraryPageSize, libraryTotal, setBusy, setError]);

  const reloadFirstPage = useCallback(async () => {
    setBusy(true);
    try {
      const page = await listLibraryClips(libraryPageSize, 0);
      resetLibraryList();
      setLibraryPage(page.items, page.total, page.offset + page.items.length);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }, [libraryPageSize, resetLibraryList, setBusy, setError, setLibraryPage]);

  const manualSearch = useCallback(
    async (query: string) => {
      if (!query.trim()) return;
      setBusy(true);
      setError(null);
      try {
        const resp = await postSearch({
          query: query.trim().slice(0, 500),
          narrative_function: "PROBLEM",
          n_results: 15,
          candidate_pool_size: 30,
        });
        setLibraryExploreCandidates(resp.results);
        setInspectedLibraryClip(null);
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
      } finally {
        setBusy(false);
      }
    },
    [setBusy, setError, setInspectedLibraryClip, setLibraryExploreCandidates],
  );

  const exploreSimilarToClip = useCallback(
    async (clip: ClipSummaryDto) => {
      const q = (clip.semantic_excerpt || clip.name || "").trim();
      if (!q) {
        setError("Este clip no tiene texto semántico para buscar similares.");
        return;
      }
      setInspectedLibraryClip(clip);
      setBusy(true);
      setError(null);
      try {
        const resp = await postSearch({
          query: q.slice(0, 500),
          narrative_function: "PROBLEM",
          n_results: 8,
          candidate_pool_size: 24,
        });
        setLibraryExploreCandidates(resp.results);
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
      } finally {
        setBusy(false);
      }
    },
    [setBusy, setError, setInspectedLibraryClip, setLibraryExploreCandidates],
  );

  return { loadMore, reloadFirstPage, manualSearch, exploreSimilarToClip };
}
