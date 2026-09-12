"""Resolución de rutas de medios en disco."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import select

from aicos.database.db import ClipRow, ProjectRow


class SqlPlaybackMediaResolver:
    def resolve_project_audio(self, session, project_id: str) -> Path | None:
        row = session.get(ProjectRow, project_id)
        if row is None or not row.audio_file_path:
            return None
        p = Path(row.audio_file_path).expanduser().resolve()
        return p if p.is_file() else None

    def resolve_clip_video(self, session, clip_id: str) -> Path | None:
        row = session.get(ClipRow, clip_id)
        if row is None:
            return None
        p = Path(row.absolute_path).expanduser().resolve()
        return p if p.is_file() else None

    def clip_exists(self, session, clip_id: str) -> bool:
        return self.resolve_clip_video(session, clip_id) is not None
