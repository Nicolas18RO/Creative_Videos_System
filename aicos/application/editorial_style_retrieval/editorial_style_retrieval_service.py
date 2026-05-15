"""Servicio de recuperación híbrida: Chroma (estructural) + SQLite (semántico opcional)."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from aicos.application.editorial_style_retrieval.ports import (
    EditorialStyleEmbeddingBatchReadPort,
    EditorialStyleVectorIndexPort,
)
from aicos.config import EditorialStyleRetrievalConfig
from aicos.domain.editorial_style_embedding.entities import EditorialStyleEmbedding
from aicos.domain.editorial_style_retrieval.entities import StyleRetrievalResult, StyleSimilarityHit
from aicos.domain.editorial_style_retrieval.scoring import cosine_similarity, hybrid_similarity_score

logger = logging.getLogger(__name__)


class EditorialStyleRetrievalService:
    def __init__(
        self,
        *,
        cfg: EditorialStyleRetrievalConfig,
        index: EditorialStyleVectorIndexPort,
        embedding_read: EditorialStyleEmbeddingBatchReadPort,
    ) -> None:
        self._cfg = cfg
        self._index = index
        self._embedding_read = embedding_read

    def index_embedding(self, emb: EditorialStyleEmbedding) -> None:
        """Indexa el vector estructural en el store vectorial (tras upsert SQLite)."""
        if not self._cfg.enabled:
            return
        meta: dict[str, Any] = {
            "digest_sha256": emb.digest_sha256,
            "fusion_mode": emb.fusion_mode,
            "structural_model_tag": emb.structural_model_tag,
        }
        try:
            self._index.upsert_structural(
                creative_id=emb.creative_id,
                structural_vector=emb.structural_vector,
                digest_text=emb.digest_text,
                metadata=meta,
            )
        except Exception:
            logger.exception("[StyleRetrieval] index upsert failed creative_id=%s", emb.creative_id)

    def remove_from_index(self, creative_id: str) -> None:
        if not self._cfg.enabled:
            return
        try:
            self._index.delete_creative(creative_id)
        except Exception:
            logger.exception("[StyleRetrieval] index delete failed creative_id=%s", creative_id)

    def retrieve_similar(
        self,
        session: Session,
        *,
        anchor_creative_id: str,
        top_k: int | None = None,
        exclude_self: bool = True,
    ) -> StyleRetrievalResult:
        if not self._cfg.enabled:
            return StyleRetrievalResult(
                anchor_creative_id=anchor_creative_id,
                hits=(),
                chroma_pool_size=0,
                used_semantic_hybrid=False,
            )
        anchor = self._embedding_read.get_many_by_creative_ids(session, [anchor_creative_id]).get(
            anchor_creative_id
        )
        if anchor is None:
            return StyleRetrievalResult(
                anchor_creative_id=anchor_creative_id,
                hits=(),
                chroma_pool_size=0,
                used_semantic_hybrid=False,
            )
        k = top_k if top_k is not None else self._cfg.top_k_default
        k = max(1, min(k, 100))
        pool = max(k, self._cfg.rerank_pool_size)
        exclude: frozenset[str] | None = frozenset([anchor_creative_id]) if exclude_self else None
        raw = self._index.query_structural(
            query_vector=anchor.structural_vector,
            n_results=pool,
            exclude_creative_ids=exclude,
        )
        if not raw:
            return StyleRetrievalResult(
                anchor_creative_id=anchor_creative_id,
                hits=(),
                chroma_pool_size=0,
                used_semantic_hybrid=False,
            )
        peer_ids = [cid for cid, _, _ in raw]
        peers_map = self._embedding_read.get_many_by_creative_ids(session, peer_ids)
        use_hybrid = self._cfg.enable_semantic_rerank and anchor.semantic_vector is not None
        scored: list[tuple[str, float, float | None, float, str]] = []
        for cid, struct_sim, _meta in raw:
            peer = peers_map.get(cid)
            peer_digest = peer.digest_sha256 if peer else ""
            sem_sim: float | None = None
            if use_hybrid and peer and peer.semantic_vector is not None:
                sem_sim = cosine_similarity(anchor.semantic_vector, peer.semantic_vector)
            hybrid = hybrid_similarity_score(
                struct_sim,
                sem_sim,
                weight_structural=self._cfg.hybrid_weight_structural,
                weight_semantic=self._cfg.hybrid_weight_semantic,
            )
            scored.append((cid, struct_sim, sem_sim, hybrid, peer_digest))
        scored.sort(key=lambda x: x[3], reverse=True)
        hits: list[StyleSimilarityHit] = []
        for rank, (cid, s_struct, s_sem, hybrid, digest_sha) in enumerate(scored[:k], start=1):
            hits.append(
                StyleSimilarityHit(
                    creative_id=cid,
                    rank=rank,
                    structural_similarity=s_struct,
                    semantic_similarity=s_sem,
                    hybrid_score=hybrid,
                    peer_digest_sha256=digest_sha,
                )
            )
        return StyleRetrievalResult(
            anchor_creative_id=anchor_creative_id,
            hits=tuple(hits),
            chroma_pool_size=len(raw),
            used_semantic_hybrid=use_hybrid,
        )
