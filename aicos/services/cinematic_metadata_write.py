"""Persistencia de filas ``clip_cinematic_metadata`` (SQLite vía SQLAlchemy en servicios)."""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from aicos.database.db import ClipCinematicMetadataRow
from aicos.domain.cinematic_metadata.entities import SourceVideoMetadata

logger = logging.getLogger(__name__)


def upsert_clip_cinematic_metadata(
    session: Session,
    clip_id: str,
    *,
    metadata: SourceVideoMetadata | None = None,
    visual_embedding_fingerprint: str | None = None,
) -> None:
    """Inserta o actualiza metadatos cinematográficos para un ``clip_id``."""
    row = session.get(ClipCinematicMetadataRow, clip_id)
    if row is None:
        row = ClipCinematicMetadataRow(clip_id=clip_id)
        session.add(row)
    if metadata is not None:
        row.source_video_id = metadata.source_video_id or None
        row.source_video_name = metadata.source_video_name or None
        row.master_reel_id = metadata.master_reel_id or None
        row.shooting_session_id = metadata.shooting_session_id or None
        row.camera_id = metadata.camera_id or None
        row.production_group = metadata.production_group or None
        row.visual_collection = metadata.visual_collection or None
        row.creation_date = metadata.creation_date or None
        row.location_tag = metadata.location_tag or None
        row.visual_cluster_id_explicit = metadata.visual_cluster_id_explicit or None
        row.provenance = metadata.provenance.value
    if visual_embedding_fingerprint is not None:
        fp = visual_embedding_fingerprint.strip()
        row.visual_embedding_fingerprint = fp[:64] if fp else None
    session.flush()
    logger.info("[CinematicMetadata] upsert clip_id=%s", clip_id)
