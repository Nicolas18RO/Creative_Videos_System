"""Puertos del motor de recomendación editorial (Fase 6.5)."""

from __future__ import annotations

from typing import Any, Protocol

from aicos.domain.editorial_style_retrieval.entities import StyleSimilarityHit


class StyleSimilarCreativesPort(Protocol):
    """Abstrae la recuperación de creativos similares en estilo (p. ej. Fase 6.4)."""

    def retrieve_hits(self, session: Any, anchor_creative_id: str, top_k: int) -> tuple[StyleSimilarityHit, ...]:
        ...
