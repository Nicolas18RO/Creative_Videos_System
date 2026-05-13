"""Factoría de puertos de lectura de metadatos cinematográficos (wiring infra)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from aicos.application.cinematic_metadata.ports import CinematicMetadataReadPort

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def create_cinematic_metadata_read_port(session: Session | None) -> CinematicMetadataReadPort | None:
    """Crea adaptador SQLite o None si no hay sesión."""
    if session is None:
        return None
    from aicos.infrastructure.cinematic_metadata.sql_clip_metadata_read_adapter import (
        SqlClipCinematicMetadataReadAdapter,
    )

    return SqlClipCinematicMetadataReadAdapter(session)
