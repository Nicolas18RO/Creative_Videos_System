"""Carga de bundle editorial desde SQLite."""

from __future__ import annotations

from sqlalchemy import select

from aicos.database.db import ClipRow, ProjectRow, SceneRow
from aicos.domain.export_pipeline.entities import ExportAssetDependency, ExportTimelineScene, ProjectEditorialBundle
from aicos.domain.export_pipeline.rules import build_asset_dependencies


class SqlExportSourceRepository:
    def load_editorial_bundle(self, session, project_id: str) -> ProjectEditorialBundle | None:
        proj = session.get(ProjectRow, project_id)
        if proj is None:
            return None
        rows = session.scalars(
            select(SceneRow).where(SceneRow.project_id == project_id).order_by(SceneRow.scene_index)
        ).all()
        scenes = tuple(
            ExportTimelineScene(
                scene_id=r.id,
                scene_index=r.scene_index,
                start_ms=r.start_ms,
                end_ms=r.end_ms,
                duration_ms=r.duration_ms,
                text=r.text or "",
                concept=r.concept or "",
                narrative_function=r.narrative_function or "NATURAL",
                selected_clip_id=r.selected_clip_id,
                is_hook=bool(r.is_hook),
            )
            for r in rows
        )
        paths = self.clip_paths_for_scenes(session, scenes)
        assets = build_asset_dependencies(scenes, paths)
        return ProjectEditorialBundle(
            project_id=proj.id,
            project_name=proj.name or "Proyecto",
            status=proj.status or "draft",
            audio_file_path=proj.audio_file_path,
            transcript_path=proj.transcript_path,
            product_name=proj.product_name,
            product_category=proj.product_category,
            target_audience=proj.target_audience,
            scenes=scenes,
            assets=assets,
        )

    def clip_paths_for_scenes(
        self, session, scenes: tuple[ExportTimelineScene, ...]
    ) -> dict[str, tuple[str, str, int | None]]:
        out: dict[str, tuple[str, str, int | None]] = {}
        for sc in scenes:
            cid = sc.selected_clip_id
            if not cid or cid in out:
                continue
            clip = session.get(ClipRow, cid)
            if clip is None:
                out[cid] = ("", "", None)
                continue
            out[cid] = (clip.absolute_path or "", clip.filename or "", clip.duration_ms)
        return out
