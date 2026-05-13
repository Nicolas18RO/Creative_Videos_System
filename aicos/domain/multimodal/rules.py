"""Reglas puras para huellas visuales (reutiliza Fase 5)."""

from __future__ import annotations

from typing import Sequence

from aicos.domain.cinematic_metadata.rules import fingerprint_visual_embedding


def visual_fingerprint_from_vector(
    vector: Sequence[float],
    *,
    model_tag: str,
) -> str:
    """Huella determinista estable para Chroma y deduplicación visual."""
    return fingerprint_visual_embedding(vector, model_tag=model_tag)
