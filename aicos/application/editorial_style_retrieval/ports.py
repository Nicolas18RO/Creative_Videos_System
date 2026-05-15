"""Puertos para indexación y lectura batch de embeddings (Fase 6.4)."""

from __future__ import annotations

from typing import Any, Protocol, Sequence

from sqlalchemy.orm import Session

from aicos.domain.editorial_style_embedding.entities import EditorialStyleEmbedding


class EditorialStyleVectorIndexPort(Protocol):
    """Índice vectorial de vectores estructurales 128-d (Chroma u otro)."""

    def upsert_structural(
        self,
        *,
        creative_id: str,
        structural_vector: tuple[float, ...],
        digest_text: str,
        metadata: dict[str, Any],
    ) -> None:
        ...

    def delete_creative(self, creative_id: str) -> None:
        ...

    def query_structural(
        self,
        *,
        query_vector: tuple[float, ...],
        n_results: int,
        exclude_creative_ids: frozenset[str] | None,
    ) -> list[tuple[str, float, dict[str, Any]]]:
        """Devuelve lista (creative_id, structural_similarity 0-1, metadata)."""
        ...


class EditorialStyleEmbeddingBatchReadPort(Protocol):
    def get_many_by_creative_ids(
        self, session: Session, creative_ids: Sequence[str]
    ) -> dict[str, EditorialStyleEmbedding]:
        ...
