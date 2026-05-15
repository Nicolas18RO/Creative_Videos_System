"""Puertos del motor de embeddings de estilo (Fase 6.3)."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from aicos.domain.editorial_style_embedding.entities import EditorialStyleEmbedding


@runtime_checkable
class SemanticStyleEmbeddingPort(Protocol):
    """Embedding semántico de un digest textual (infra: sentence-transformers, etc.)."""

    def embed_digest(self, text: str) -> tuple[float, ...]:
        ...


@runtime_checkable
class EditorialStyleEmbeddingPersistencePort(Protocol):
    """Persistencia de embeddings de estilo (infra SQLite)."""

    def upsert(self, session: Any, embedding: EditorialStyleEmbedding) -> None:
        ...

    def get_by_creative_id(self, session: Any, creative_id: str) -> EditorialStyleEmbedding | None:
        ...
