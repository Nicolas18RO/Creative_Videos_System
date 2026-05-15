"""Dominio: recuperación por similitud de estilo editorial (Fase 6.4)."""

from aicos.domain.editorial_style_retrieval.entities import StyleRetrievalResult, StyleSimilarityHit
from aicos.domain.editorial_style_retrieval.scoring import cosine_similarity, hybrid_similarity_score

__all__ = [
    "StyleRetrievalResult",
    "StyleSimilarityHit",
    "cosine_similarity",
    "hybrid_similarity_score",
]
