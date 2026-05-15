"""Resultados puros de búsqueda por estilo editorial (sin infraestructura)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StyleSimilarityHit:
    """Un creativo vecino en el espacio de estilo editorial."""

    creative_id: str
    rank: int
    structural_similarity: float
    semantic_similarity: float | None
    hybrid_score: float
    peer_digest_sha256: str


@dataclass(frozen=True, slots=True)
class StyleRetrievalResult:
    """Resultado de una consulta de similitud editorial."""

    anchor_creative_id: str
    hits: tuple[StyleSimilarityHit, ...]
    chroma_pool_size: int
    used_semantic_hybrid: bool
