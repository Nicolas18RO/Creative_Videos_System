"""Factoría Fase 6.4 — recuperación por similitud de estilo editorial."""

from __future__ import annotations

import logging

from aicos.application.editorial_style_retrieval.editorial_style_retrieval_service import (
    EditorialStyleRetrievalService,
)
from aicos.config import AppConfig, get_config
from aicos.domain.editorial_style_embedding.entities import EditorialStyleEmbedding
from aicos.infrastructure.editorial_style_embedding.sql_editorial_style_embedding_repository import (
    SqlEditorialStyleEmbeddingRepository,
)

logger = logging.getLogger(__name__)


def build_editorial_style_retrieval_service(app_cfg: AppConfig | None = None) -> EditorialStyleRetrievalService:
    cfg = app_cfg or get_config()
    rc = cfg.editorial_style_retrieval
    sql_repo = SqlEditorialStyleEmbeddingRepository()
    if not rc.enabled:
        from aicos.infrastructure.editorial_style_retrieval.null_editorial_style_index import (
            NullEditorialStyleVectorIndex,
        )

        idx = NullEditorialStyleVectorIndex()
    else:
        from aicos.infrastructure.editorial_style_retrieval.chroma_editorial_style_index import (
            ChromaEditorialStyleIndexAdapter,
        )

        idx = ChromaEditorialStyleIndexAdapter(rc)
    return EditorialStyleRetrievalService(cfg=rc, index=idx, embedding_read=sql_repo)


def maybe_index_style_embedding(emb: EditorialStyleEmbedding, app_cfg: AppConfig | None = None) -> None:
    """Tras persistir en SQLite, indexa el vector estructural en Chroma (si la fase 6.4 está activa)."""
    cfg = app_cfg or get_config()
    if not cfg.editorial_style_retrieval.enabled:
        return
    try:
        svc = build_editorial_style_retrieval_service(cfg)
        svc.index_embedding(emb)
    except Exception as e:
        logger.warning("[StyleRetrieval] index skipped creative=%s error=%s", emb.creative_id, e)
