"""Factoría del Global Context Engine (composición en capa servicios)."""

from __future__ import annotations

from aicos.application.context.global_context_service import GlobalContextService
from aicos.application.context.rule_based_global_context_provider import (
    RuleBasedGlobalContextProvider,
    RuleBasedNarrativeInferenceProvider,
)


def build_global_context_service(*, with_embedding: bool = True) -> GlobalContextService:
    """Ensambla servicio local-first (reglas + embedding opcional).

    El adaptador de embeddings importa ``torch`` vía ``Embedder``; se omite si
    ``with_embedding=False`` (p. ej. tests sin dependencias pesadas).
    """
    emb = None
    if with_embedding:
        from aicos.infrastructure.context.local_global_embedding_adapter import LocalGlobalEmbeddingAdapter

        emb = LocalGlobalEmbeddingAdapter()
    return GlobalContextService(
        analyzer=RuleBasedGlobalContextProvider(),
        narrative=RuleBasedNarrativeInferenceProvider(),
        embedding=emb,
    )
