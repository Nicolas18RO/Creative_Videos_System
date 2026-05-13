"""Mapeo ORM → dominio para metadatos cinematográficos (capa servicios)."""

from __future__ import annotations

from aicos.database.db import ClipCinematicMetadataRow
from aicos.domain.cinematic_metadata.entities import SourceVideoMetadata
from aicos.domain.cinematic_metadata.enums import CinematicMetadataProvenance


def clip_cinematic_row_to_domain(row: ClipCinematicMetadataRow | None) -> SourceVideoMetadata | None:
    """Convierte fila SQLite en entidad de dominio."""
    if row is None:
        return None
    raw = (row.provenance or "explicit").strip().lower()
    try:
        prov = CinematicMetadataProvenance(raw)
    except ValueError:
        prov = CinematicMetadataProvenance.EXPLICIT
    dom = SourceVideoMetadata(
        source_video_id=(row.source_video_id or "").strip(),
        source_video_name=(row.source_video_name or "").strip(),
        master_reel_id=(row.master_reel_id or "").strip(),
        shooting_session_id=(row.shooting_session_id or "").strip(),
        camera_id=(row.camera_id or "").strip(),
        production_group=(row.production_group or "").strip(),
        visual_collection=(row.visual_collection or "").strip(),
        creation_date=(row.creation_date or "").strip(),
        location_tag=(row.location_tag or "").strip(),
        visual_cluster_id_explicit=(row.visual_cluster_id_explicit or "").strip(),
        provenance=prov,
    )
    if not dom.has_explicit_source_key() and not any(
        (
            dom.source_video_name,
            dom.shooting_session_id,
            dom.camera_id,
            dom.visual_cluster_id_explicit,
            (row.visual_embedding_fingerprint or "").strip(),
        )
    ):
        return None
    return dom
