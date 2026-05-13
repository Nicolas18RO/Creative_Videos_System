"""Adaptador de infraestructura: embeddings locales para contexto global."""

from __future__ import annotations

import hashlib
import logging
import time
from dataclasses import dataclass

from aicos.application.context.ports import GlobalEmbeddingPort
from aicos.core.embedder import Embedder

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class LocalGlobalEmbeddingAdapter(GlobalEmbeddingPort):
    """Usa ``Embedder`` (sentence-transformers / config) sin APIs externas."""

    _embedder: Embedder | None = None

    def _get_embedder(self) -> Embedder:
        if self._embedder is None:
            self._embedder = Embedder()
        return self._embedder

    def embed_context(self, embedding_text: str) -> tuple[list[float], str]:
        t0 = time.perf_counter()
        vec = self._get_embedder().embed(embedding_text)
        digest = hashlib.sha256(embedding_text.encode("utf-8", errors="ignore")).hexdigest()[:28]
        eid = f"gc_local_{digest}"
        elapsed_ms = (time.perf_counter() - t0) * 1000
        logger.info(
            "[GlobalContext] embedding_infra provider=local dim=%s elapsed_ms=%.1f",
            len(vec),
            elapsed_ms,
        )
        return vec, eid
