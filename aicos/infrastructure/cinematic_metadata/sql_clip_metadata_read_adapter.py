"""Adaptador de lectura: SQLite → puerto de metadatos cinematográficos."""

from __future__ import annotations

import logging
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from aicos.application.cinematic_metadata.ports import CinematicMetadataReadPort
from aicos.database.db import ClipCinematicMetadataRow
from aicos.domain.cinematic_metadata.entities import SourceVideoMetadata
from aicos.services.cinematic_metadata_mapping import clip_cinematic_row_to_domain

logger = logging.getLogger(__name__)


class SqlClipCinematicMetadataReadAdapter(CinematicMetadataReadPort):
    """Implementación infra del puerto ``CinematicMetadataReadPort``."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_clip_id(self, clip_id: str) -> SourceVideoMetadata | None:
        row = self._session.get(ClipCinematicMetadataRow, clip_id)
        return clip_cinematic_row_to_domain(row)

    def get_many_by_clip_ids(self, clip_ids: Sequence[str]) -> dict[str, SourceVideoMetadata]:
        if not clip_ids:
            return {}
        stmt = select(ClipCinematicMetadataRow).where(ClipCinematicMetadataRow.clip_id.in_(tuple(clip_ids)))
        rows = list(self._session.scalars(stmt).all())
        out: dict[str, SourceVideoMetadata] = {}
        for r in rows:
            dom = clip_cinematic_row_to_domain(r)
            if dom is not None:
                out[r.clip_id] = dom
        logger.debug("[CinematicMetadata] batch_loaded count=%s", len(out))
        return out
