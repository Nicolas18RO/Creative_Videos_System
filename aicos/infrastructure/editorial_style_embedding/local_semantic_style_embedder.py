"""Adaptador semántico local (sentence-transformers vía ``Embedder``)."""

from __future__ import annotations

import logging

from aicos.application.editorial_style_embedding.ports import SemanticStyleEmbeddingPort
from aicos.core.embedder import Embedder

logger = logging.getLogger(__name__)


class LocalSemanticStyleEmbedder(SemanticStyleEmbeddingPort):
    def __init__(self, *, embedder: Embedder | None = None) -> None:
        self._embedder = embedder or Embedder()

    def embed_digest(self, text: str) -> tuple[float, ...]:
        vec = self._embedder.embed(text)
        out = tuple(float(x) for x in vec)
        logger.debug("[StyleEmbedding] semantic_dim=%s", len(out))
        return out
