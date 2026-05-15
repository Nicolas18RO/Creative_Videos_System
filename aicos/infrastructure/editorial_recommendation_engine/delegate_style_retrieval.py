"""Delegación a ``EditorialStyleRetrievalService`` sin acoplar el dominio 6.5 al de Chroma."""

from __future__ import annotations

from typing import Any

from aicos.application.editorial_style_retrieval.editorial_style_retrieval_service import EditorialStyleRetrievalService
from aicos.domain.editorial_style_retrieval.entities import StyleSimilarityHit


class DelegatingStyleSimilarCreativesPort:
    def __init__(self, retrieval: EditorialStyleRetrievalService) -> None:
        self._retrieval = retrieval

    def retrieve_hits(self, session: Any, anchor_creative_id: str, top_k: int) -> tuple[StyleSimilarityHit, ...]:
        res = self._retrieval.retrieve_similar(
            session,
            anchor_creative_id=anchor_creative_id,
            top_k=top_k,
            exclude_self=True,
        )
        return res.hits
