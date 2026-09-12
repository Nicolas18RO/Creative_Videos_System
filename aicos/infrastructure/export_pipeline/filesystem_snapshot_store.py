"""Snapshots editoriales en disco (~/.aicos/exports/{project_id}/snapshots/)."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from aicos.domain.export_pipeline.entities import BUNDLE_FORMAT_VERSION, ExportTimelineScene, ProjectEditorialBundle


class FilesystemSnapshotStore:
    def __init__(self, exports_root: Path) -> None:
        self._root = exports_root.resolve()
        self._root.mkdir(parents=True, exist_ok=True)

    def _project_dir(self, project_id: str) -> Path:
        pid = project_id.strip()
        if not pid or ".." in pid or "/" in pid or "\\" in pid:
            raise ValueError("invalid_project_id")
        d = (self._root / pid / "snapshots").resolve()
        root = self._root.resolve()
        if not str(d).startswith(str(root)):
            raise ValueError("invalid_snapshot_path")
        d.mkdir(parents=True, exist_ok=True)
        return d

    def save_snapshot(self, bundle: ProjectEditorialBundle, *, snapshot_id: str, created_at: datetime) -> str:
        d = self._project_dir(bundle.project_id)
        path = d / f"{snapshot_id}.json"
        payload = self._bundle_to_json(bundle, snapshot_id=snapshot_id, created_at=created_at)
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return str(path)

    def list_snapshots(self, project_id: str) -> list[tuple[str, datetime, str]]:
        d = self._project_dir(project_id)
        out: list[tuple[str, datetime, str]] = []
        for p in sorted(d.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
            sid = p.stem
            try:
                raw = json.loads(p.read_text(encoding="utf-8"))
                created = raw.get("created_at")
                dt = datetime.fromisoformat(created) if created else datetime.fromtimestamp(p.stat().st_mtime)
            except (json.JSONDecodeError, ValueError, OSError):
                dt = datetime.fromtimestamp(p.stat().st_mtime)
            out.append((sid, dt, str(p)))
        return out

    def load_snapshot(self, project_id: str, snapshot_id: str) -> ProjectEditorialBundle | None:
        sid = snapshot_id.strip()
        if not sid or ".." in sid or "/" in sid:
            raise ValueError("invalid_snapshot_id")
        path = self._project_dir(project_id) / f"{sid}.json"
        if not path.is_file():
            return None
        raw = json.loads(path.read_text(encoding="utf-8"))
        return self._json_to_bundle(raw)

    @staticmethod
    def _bundle_to_json(bundle: ProjectEditorialBundle, *, snapshot_id: str, created_at: datetime) -> dict:
        return {
            "format_version": bundle.format_version,
            "snapshot_id": snapshot_id,
            "created_at": created_at.isoformat(),
            "project_id": bundle.project_id,
            "project_name": bundle.project_name,
            "status": bundle.status,
            "audio_file_path": bundle.audio_file_path,
            "transcript_path": bundle.transcript_path,
            "product_name": bundle.product_name,
            "product_category": bundle.product_category,
            "target_audience": bundle.target_audience,
            "scenes": [
                {
                    "scene_id": s.scene_id,
                    "scene_index": s.scene_index,
                    "start_ms": s.start_ms,
                    "end_ms": s.end_ms,
                    "duration_ms": s.duration_ms,
                    "text": s.text,
                    "concept": s.concept,
                    "narrative_function": s.narrative_function,
                    "selected_clip_id": s.selected_clip_id,
                    "is_hook": s.is_hook,
                }
                for s in bundle.scenes
            ],
        }

    @staticmethod
    def _json_to_bundle(raw: dict) -> ProjectEditorialBundle:
        scenes = tuple(
            ExportTimelineScene(
                scene_id=s["scene_id"],
                scene_index=int(s["scene_index"]),
                start_ms=int(s["start_ms"]),
                end_ms=int(s["end_ms"]),
                duration_ms=int(s["duration_ms"]),
                text=s.get("text") or "",
                concept=s.get("concept") or "",
                narrative_function=s.get("narrative_function") or "NATURAL",
                selected_clip_id=s.get("selected_clip_id"),
                is_hook=bool(s.get("is_hook")),
            )
            for s in raw.get("scenes") or []
        )
        created_raw = raw.get("created_at")
        created = datetime.fromisoformat(created_raw) if created_raw else None
        return ProjectEditorialBundle(
            project_id=raw["project_id"],
            project_name=raw.get("project_name") or "Proyecto",
            status=raw.get("status") or "draft",
            audio_file_path=raw.get("audio_file_path"),
            transcript_path=raw.get("transcript_path"),
            product_name=raw.get("product_name"),
            product_category=raw.get("product_category"),
            target_audience=raw.get("target_audience"),
            scenes=scenes,
            assets=(),
            format_version=raw.get("format_version") or BUNDLE_FORMAT_VERSION,
            snapshot_id=raw.get("snapshot_id"),
            created_at=created,
        )
