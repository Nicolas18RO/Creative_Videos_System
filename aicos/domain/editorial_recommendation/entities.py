"""Entidades del plan editorial recomendado (Fase 6.5)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StyleMemoryPeerRef:
    """Creativo vecino en memoria editorial (similitud de estilo)."""

    creative_id: str
    hybrid_score: float


@dataclass(frozen=True, slots=True)
class EditorialRecommendationItem:
    """Una decisión o guía editorial concreta y auditable."""

    recommendation_id: str
    kind: str
    summary: str
    detail: str
    confidence: float
    sources: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ClipSearchContextHint:
    """Contexto listo para acoplar a ``SearchRequest`` (RAG editorial sobre el catálogo)."""

    query_line: str
    global_query_enrichment: str
    narrative_function_hint: str | None
    is_hook_context: bool
    semantic_tags: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class EditorialRecommendationPlan:
    """Plan agregado: memoria de estilo + guías + puente hacia búsqueda de clips."""

    anchor_creative_id: str
    items: tuple[EditorialRecommendationItem, ...]
    clip_search_hint: ClipSearchContextHint | None
    style_memory_peers: tuple[StyleMemoryPeerRef, ...]
