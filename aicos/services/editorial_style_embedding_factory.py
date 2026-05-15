"""Factoría Fase 6.3 — embeddings de estilo editorial."""

from __future__ import annotations

import logging
from dataclasses import replace
from typing import Any

from aicos.application.editorial_style_embedding.editorial_style_embedding_service import EditorialStyleEmbeddingService
from aicos.config import AppConfig, get_config
from aicos.domain.editorial_dataset.entities import CreativeTimeline
from aicos.infrastructure.editorial_style_embedding.sql_editorial_style_embedding_repository import (
    SqlEditorialStyleEmbeddingRepository,
)

logger = logging.getLogger(__name__)


def build_editorial_style_embedding_service(app_cfg: AppConfig | None = None) -> EditorialStyleEmbeddingService:
    cfg = app_cfg or get_config()
    ec = cfg.editorial_style_embedding
    sem = None
    if ec.enable_semantic_embedding:
        from aicos.infrastructure.editorial_style_embedding.local_semantic_style_embedder import (
            LocalSemanticStyleEmbedder,
        )

        sem = LocalSemanticStyleEmbedder()
    return EditorialStyleEmbeddingService(ec, semantic=sem)


def maybe_attach_style_embedding(
    session: Any | None,
    timeline: CreativeTimeline,
    app_cfg: AppConfig | None = None,
) -> CreativeTimeline:
    cfg = app_cfg or get_config()
    ec = cfg.editorial_style_embedding
    if not ec.enabled:
        return timeline
    try:
        svc = build_editorial_style_embedding_service(cfg)
        emb = svc.embed_timeline(timeline, pattern_engine_report=timeline.pattern_engine_report)
        timeline = replace(timeline, style_embedding=emb)
        if session is not None:
            SqlEditorialStyleEmbeddingRepository().upsert(session, emb)
            from aicos.services.editorial_style_retrieval_factory import maybe_index_style_embedding

            maybe_index_style_embedding(emb, cfg)
    except Exception as e:
        logger.warning("[StyleEmbedding] skipped creative=%s error=%s", timeline.creative_id, e)
    return timeline
