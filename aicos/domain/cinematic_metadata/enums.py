"""Procedencia de metadatos (dominio puro)."""

from __future__ import annotations

from enum import Enum


class CinematicMetadataProvenance(str, Enum):
    """Origen del registro para auditoría y mezcla de señales."""

    EXPLICIT = "explicit"
    IMPORTED = "imported"
    INFERRED = "inferred"
    HYBRID = "hybrid"
