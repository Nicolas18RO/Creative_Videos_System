"""Índice nulo cuando la recuperación por estilo está desactivada."""

from __future__ import annotations

from typing import Any


class NullEditorialStyleVectorIndex:
    def upsert_structural(
        self,
        *,
        creative_id: str,
        structural_vector: tuple[float, ...],
        digest_text: str,
        metadata: dict[str, Any],
    ) -> None:
        return

    def delete_creative(self, creative_id: str) -> None:
        return

    def query_structural(
        self,
        *,
        query_vector: tuple[float, ...],
        n_results: int,
        exclude_creative_ids: frozenset[str] | None,
    ) -> list[tuple[str, float, dict[str, Any]]]:
        return []
