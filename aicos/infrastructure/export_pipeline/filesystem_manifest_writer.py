"""Escritura de manifests JSON en el árbol de exports."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


class FilesystemManifestWriter:
    def __init__(self, exports_root: Path) -> None:
        self._root = exports_root.resolve()
        self._root.mkdir(parents=True, exist_ok=True)

    def _manifests_dir(self, project_id: str) -> Path:
        pid = project_id.strip()
        if not pid or ".." in pid:
            raise ValueError("invalid_project_id")
        d = (self._root / pid / "manifests").resolve()
        d.mkdir(parents=True, exist_ok=True)
        return d

    def write_capcut_manifest(self, project_id: str, payload: dict) -> str:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        path = self._manifests_dir(project_id) / f"capcut_{ts}.json"
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return str(path)

    def write_export_manifest(self, project_id: str, payload: dict) -> str:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        path = self._manifests_dir(project_id) / f"export_{ts}.json"
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return str(path)
