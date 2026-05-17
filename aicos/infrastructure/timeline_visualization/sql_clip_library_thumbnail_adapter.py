"""Resuelve thumbnails de la biblioteca de clips por clip_id."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from aicos.application.timeline_visualization.ports import ClipLibraryThumbnailPort
from aicos.database.db import ClipRow


class SqlClipLibraryThumbnailAdapter(ClipLibraryThumbnailPort):
    def resolve_thumbnail_path(self, session: Any, clip_id: str) -> str | None:
        cid = (clip_id or "").strip()
        if not cid or cid.startswith("unassigned_"):
            return None
        row = session.get(ClipRow, cid)
        if row is None:
            return None
        p = (row.thumbnail_path or "").strip()
        return p or None
