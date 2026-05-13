"""Escritura multimodal vía ``VectorStore`` (Chroma encapsulado en core)."""

from __future__ import annotations

import logging
import time
from typing import Any

from aicos.application.multimodal_retrieval.ports import ChromaMultimodalWritePort
from aicos.config import MultimodalRetrievalConfig, get_config
from aicos.core.vector_store import VectorStore
from aicos.domain.multimodal_retrieval.entities import ChromaFingerprintPayload

logger = logging.getLogger(__name__)

_MAX_ATTEMPTS = 3
_BACKOFF_S = 0.08


class ChromaMultimodalWriter(ChromaMultimodalWritePort):
    """Fusiona metadatos sin reindex completo; embedding textual se conserva salvo política explícita."""

    def __init__(
        self,
        *,
        store: VectorStore | None = None,
        retrieval_cfg: MultimodalRetrievalConfig | None = None,
    ) -> None:
        self._store = store or VectorStore()
        self._cfg = retrieval_cfg or get_config().multimodal_retrieval

    def upsert_multimodal(
        self,
        session: Any,
        payloads: list[ChromaFingerprintPayload],
        *,
        update_existing: bool,
    ) -> None:
        if not payloads:
            return
        ids = [p.chroma_id for p in payloads]
        existing = self._store.get_clip_payloads(ids)
        ids_out: list[str] = []
        docs: list[str] = []
        embs: list[list[float]] = []
        metas: list[dict[str, Any]] = []
        for p in payloads:
            cid = p.chroma_id
            pl = existing.get(cid)
            if not pl or not pl.get("embedding"):
                logger.info("[ChromaUpsert] clip=%s success=False reason=missing_chroma_vector", cid)
                continue
            old_meta = pl.get("metadata") or {}
            flat_old = {str(k): str(v) if v is not None else "" for k, v in old_meta.items()}
            merged = dict(flat_old)
            merged.update(p.metadata)
            emb = list(map(float, pl["embedding"]))
            if (
                update_existing
                and self._cfg.allow_visual_embedding_overwrite
                and p.embedding is not None
                and len(p.embedding) == len(emb)
            ):
                emb = list(map(float, p.embedding))
            ids_out.append(cid)
            docs.append(str(pl.get("document") or ""))
            embs.append(emb)
            metas.append(merged)
        if not ids_out:
            return
        last_exc: Exception | None = None
        for attempt in range(1, _MAX_ATTEMPTS + 1):
            try:
                self._store.update_clip_documents_metadatas(
                    ids=ids_out,
                    documents=docs,
                    embeddings=embs,
                    metadatas=metas,
                )
                for cid in ids_out:
                    logger.info("[ChromaUpsert] clip=%s success=True attempt=%s", cid, attempt)
                return
            except Exception as e:
                last_exc = e
                logger.warning(
                    "[ChromaUpsert] batch_retry attempt=%s/%s error=%s",
                    attempt,
                    _MAX_ATTEMPTS,
                    e,
                )
                time.sleep(_BACKOFF_S * attempt)
        if last_exc is not None:
            raise last_exc
