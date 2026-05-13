"""Persistencia de embeddings visuales y huella en metadatos cinematográficos."""

from __future__ import annotations

import json
import logging

from sqlalchemy.orm import Session

from aicos.database.db import ClipVisualEmbeddingRow
from aicos.domain.multimodal.entities import VisualEmbedding
from aicos.services import cinematic_metadata_write

logger = logging.getLogger(__name__)


def persist_clip_visual_embedding(session: Session, embedding: VisualEmbedding) -> None:
    """Guarda vector JSON y actualiza ``visual_embedding_fingerprint`` en cine metadata."""
    row = session.get(ClipVisualEmbeddingRow, embedding.clip_id)
    if row is None:
        row = ClipVisualEmbeddingRow(clip_id=embedding.clip_id)
        session.add(row)
    row.embedding_json = json.dumps(list(embedding.embedding_vector))
    row.model_tag = embedding.embedding_model[:160]
    row.dimension = embedding.embedding_dimension
    row.fingerprint = (embedding.visual_fingerprint or "")[:64]
    session.flush()
    cinematic_metadata_write.upsert_clip_cinematic_metadata(
        session,
        embedding.clip_id,
        metadata=None,
        visual_embedding_fingerprint=embedding.visual_fingerprint,
    )
    logger.info(
        "[MultimodalPersist] clip_id=%s dim=%s fp=%s",
        embedding.clip_id,
        embedding.embedding_dimension,
        (embedding.visual_fingerprint or "")[:16],
    )
