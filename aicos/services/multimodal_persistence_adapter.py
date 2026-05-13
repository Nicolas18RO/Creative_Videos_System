"""Adaptador de persistencia que implementa el puerto de aplicación."""

from __future__ import annotations

from typing import Any

from aicos.domain.multimodal.entities import VisualEmbedding
from aicos.services import visual_embedding_persistence


class SqlVisualEmbeddingPersistenceAdapter:
    """Delega en ``visual_embedding_persistence`` (servicios)."""

    def persist_visual_embedding(self, session: Any, embedding: VisualEmbedding) -> None:
        visual_embedding_persistence.persist_clip_visual_embedding(session, embedding)
