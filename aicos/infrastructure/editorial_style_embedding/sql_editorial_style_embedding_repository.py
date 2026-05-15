"""Persistencia SQLite de embeddings de estilo editorial (Fase 6.3)."""

from __future__ import annotations

import logging
import uuid
from typing import Sequence

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from aicos.application.editorial_style_embedding.ports import EditorialStyleEmbeddingPersistencePort
from aicos.database.db import EditorialStyleEmbeddingRow
from aicos.domain.editorial_style_embedding.entities import EditorialStyleEmbedding

logger = logging.getLogger(__name__)


class SqlEditorialStyleEmbeddingRepository(EditorialStyleEmbeddingPersistencePort):
    def __init__(self) -> None:
        pass

    def upsert(self, session: Session, embedding: EditorialStyleEmbedding) -> None:
        session.execute(
            delete(EditorialStyleEmbeddingRow).where(
                EditorialStyleEmbeddingRow.creative_id == embedding.creative_id
            )
        )
        row = EditorialStyleEmbeddingRow(
            id=str(uuid.uuid4()),
            creative_id=embedding.creative_id,
            structural_vector_json=list(embedding.structural_vector),
            semantic_vector_json=list(embedding.semantic_vector) if embedding.semantic_vector else None,
            fused_vector_json=list(embedding.fused_vector),
            digest_text=embedding.digest_text,
            digest_sha256=embedding.digest_sha256,
            structural_model_tag=embedding.structural_model_tag,
            semantic_model_tag=embedding.semantic_model_tag,
            fusion_mode=embedding.fusion_mode,
        )
        session.add(row)
        session.flush()
        logger.debug("[StyleEmbedding] upsert creative_id=%s", embedding.creative_id)

    def get_by_creative_id(self, session: Session, creative_id: str) -> EditorialStyleEmbedding | None:
        row = session.scalars(
            select(EditorialStyleEmbeddingRow).where(EditorialStyleEmbeddingRow.creative_id == creative_id)
        ).first()
        if row is None:
            return None
        return self._row_to_entity(row)

    def get_many_by_creative_ids(
        self, session: Session, creative_ids: Sequence[str]
    ) -> dict[str, EditorialStyleEmbedding]:
        ids = [str(x) for x in creative_ids if x]
        if not ids:
            return {}
        rows = session.scalars(
            select(EditorialStyleEmbeddingRow).where(EditorialStyleEmbeddingRow.creative_id.in_(ids))
        ).all()
        return {row.creative_id: self._row_to_entity(row) for row in rows}

    @staticmethod
    def _row_to_entity(row: EditorialStyleEmbeddingRow) -> EditorialStyleEmbedding:
        sem = tuple(float(x) for x in row.semantic_vector_json) if row.semantic_vector_json else None
        return EditorialStyleEmbedding(
            creative_id=row.creative_id,
            structural_vector=tuple(float(x) for x in row.structural_vector_json),
            semantic_vector=sem,
            fused_vector=tuple(float(x) for x in row.fused_vector_json),
            digest_text=row.digest_text or "",
            digest_sha256=row.digest_sha256 or "",
            structural_model_tag=row.structural_model_tag or "",
            semantic_model_tag=row.semantic_model_tag,
            fusion_mode=row.fusion_mode or "concat_l2",
        )
