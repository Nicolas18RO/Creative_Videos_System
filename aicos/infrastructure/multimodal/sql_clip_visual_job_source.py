"""Fuente de trabajo batch: clips vídeo desde SQLite."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import not_, select

from aicos.database.db import ClipRow, ClipVisualEmbeddingRow
from aicos.domain.multimodal.entities import ClipVisualJobTarget

logger = logging.getLogger(__name__)


class SqlClipVisualJobSource:
    """Lista clips vídeo con ruta absoluta; opcionalmente excluye ya indexados por modelo."""

    def __init__(self, *, model_tag: str, skip_existing_same_model: bool) -> None:
        self._model_tag = model_tag
        self._skip = skip_existing_same_model

    def iter_targets(
        self,
        session: Any,
        *,
        limit: int,
        rescan_all: bool,
    ) -> list[ClipVisualJobTarget]:
        stmt = select(ClipRow).where(ClipRow.asset_kind == "video")
        if self._skip and not rescan_all:
            sub = select(ClipVisualEmbeddingRow.clip_id).where(
                ClipVisualEmbeddingRow.model_tag == self._model_tag
            )
            stmt = stmt.where(not_(ClipRow.id.in_(sub)))
        stmt = stmt.order_by(ClipRow.relative_path).limit(max(1, limit))
        rows = list(session.scalars(stmt).all())
        out: list[ClipVisualJobTarget] = []
        for r in rows:
            ap = (r.absolute_path or "").strip()
            if not ap:
                continue
            out.append(ClipVisualJobTarget(clip_id=r.id, absolute_path=ap))
        logger.debug("[ClipVisualJobSource] limit=%s returned=%s", limit, len(out))
        return out
