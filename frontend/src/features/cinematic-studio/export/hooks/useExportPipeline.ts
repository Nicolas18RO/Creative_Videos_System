import { useCallback, useEffect, useState } from "react";

import {
  downloadCapCutManifestJson,
  fetchCapCutManifest,
  fetchExportManifest,
  listProjectSnapshots,
  persistProjectSnapshot,
  restoreProjectSnapshot,
  writeCapCutManifestFile,
} from "../api/exportPipelineApi";
import { capcutReadinessSummary, exportManifestSummary } from "../presentation/exportPresentation";
import type { CapCutManifestDto, ExportManifestDto, ProjectSnapshotMetaDto } from "../types/export";

export function useExportPipeline(projectId: string | null) {
  const [capcut, setCapcut] = useState<CapCutManifestDto | null>(null);
  const [manifest, setManifest] = useState<ExportManifestDto | null>(null);
  const [snapshots, setSnapshots] = useState<ProjectSnapshotMetaDto[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastWrittenPath, setLastWrittenPath] = useState<string | null>(null);

  const reload = useCallback(async () => {
    if (!projectId) {
      setCapcut(null);
      setManifest(null);
      setSnapshots([]);
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const [cc, mf, snaps] = await Promise.all([
        fetchCapCutManifest(projectId),
        fetchExportManifest(projectId),
        listProjectSnapshots(projectId),
      ]);
      setCapcut(cc);
      setManifest(mf);
      setSnapshots(snaps.snapshots ?? []);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }, [projectId]);

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      if (!projectId) {
        setCapcut(null);
        setManifest(null);
        setSnapshots([]);
        return;
      }
      setBusy(true);
      setError(null);
      try {
        const [cc, mf, snaps] = await Promise.all([
          fetchCapCutManifest(projectId),
          fetchExportManifest(projectId),
          listProjectSnapshots(projectId),
        ]);
        if (cancelled) return;
        setCapcut(cc);
        setManifest(mf);
        setSnapshots(snaps.snapshots ?? []);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      } finally {
        if (!cancelled) setBusy(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [projectId]);

  const saveSnapshot = useCallback(async () => {
    if (!projectId) return;
    setBusy(true);
    setError(null);
    try {
      await persistProjectSnapshot(projectId);
      await reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }, [projectId, reload]);

  const restoreSnapshot = useCallback(
    async (snapshotId: string) => {
      if (!projectId) return;
      setBusy(true);
      setError(null);
      try {
        await restoreProjectSnapshot(projectId, snapshotId);
        await reload();
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
      } finally {
        setBusy(false);
      }
    },
    [projectId, reload],
  );

  const writeCapCutToDisk = useCallback(async () => {
    if (!projectId) return;
    setBusy(true);
    setError(null);
    try {
      const { path } = await writeCapCutManifestFile(projectId);
      setLastWrittenPath(path);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }, [projectId]);

  const downloadCapCut = useCallback(async () => {
    if (!projectId) return;
    setError(null);
    try {
      await downloadCapCutManifestJson(projectId);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, [projectId]);

  const readiness = capcut ? capcutReadinessSummary(capcut) : null;
  const manifestHint = manifest ? exportManifestSummary(manifest) : null;

  return {
    capcut,
    manifest,
    snapshots,
    readiness,
    manifestHint,
    busy,
    error,
    lastWrittenPath,
    reload,
    saveSnapshot,
    restoreSnapshot,
    writeCapCutToDisk,
    downloadCapCut,
  };
}
