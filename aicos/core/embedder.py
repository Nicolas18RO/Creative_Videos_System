"""Fachada de embeddings: delega en proveedor local u OpenAI según `config.yaml`."""

from __future__ import annotations

import logging
from typing import Sequence

from aicos.core.embeddings.factory import build_embedding_provider

logger = logging.getLogger(__name__)


class Embedder:
    """Misma API pública: `embed` / `embed_batch` sobre el proveedor configurado."""

    def __init__(self, api_key: str | None = None) -> None:
        self._provider = build_embedding_provider(api_key=api_key)
        dim = self._provider.embedding_dimension
        logger.debug("Embedder listo (dim conocida=%s)", dim)

    @property
    def embedding_dimension(self) -> int | None:
        return self._provider.embedding_dimension

    def embed(self, text: str) -> list[float]:
        return self._provider.embed(text)

    def embed_batch(self, texts: Sequence[str], batch_size: int | None = None) -> list[list[float]]:
        return self._provider.embed_batch(texts, batch_size=batch_size)
