"""Tipos de evento de uso de clip (dominio puro)."""

from __future__ import annotations

from enum import Enum


class ClipUsageType(str, Enum):
    """Clasificación editorial del registro de uso."""

    SELECTION = "selection"
    CANDIDATE_POOL = "candidate_pool"
    REJECTION = "rejection"
    PREVIEW = "preview"
