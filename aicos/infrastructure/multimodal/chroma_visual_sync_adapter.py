"""Sincroniza metadatos visuales en Chroma tras persistir embeddings."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from aicos.core.vector_store import VectorStore
from aicos.database.db import ClipCinematicMetadataRow, ClipRow
from aicos.services.chroma_clip_metadata import build_chroma_metadata_bundle

logger = logging.getLogger(__name__)


class ChromaVisualMetadataSyncAdapter:
    """Preserva documento y embedding textual; fusiona ``cm_*``."""

    def __init__(self, *, store: VectorStore) -> None:
        self._store = store

    def sync_clips(self, session: Any, clip_ids: list[str]) -> None:
        if not clip_ids:
            return
        sess: Session = session
        payloads = self._store.get_clip_payloads(clip_ids)
        ids_out: list[str] = []
        docs: list[str] = []
        embs: list[list[float]] = []
        metas: list[dict] = []
        for cid in clip_ids:
            pl = payloads.get(cid)
            if not pl or not pl.get("embedding"):
                logger.info("[ChromaVisualSync] skip_missing_vector clip_id=%s", cid)
                continue
            row = sess.get(ClipRow, cid)
            if row is None:
                continue
            cm = sess.get(ClipCinematicMetadataRow, cid)
            merged = build_chroma_metadata_bundle(row, cm)
            old_meta = pl.get("metadata") or {}
            flat_old = {str(k): str(v) if v is not None else "" for k, v in old_meta.items()}
            flat_old.update(merged)
            ids_out.append(cid)
            docs.append(str(pl.get("document") or ""))
            embs.append(list(map(float, pl["embedding"])))
            metas.append(flat_old)
        if not ids_out:
            return
        self._store.update_clip_documents_metadatas(
            ids=ids_out,
            documents=docs,
            embeddings=embs,
            metadatas=metas,
        )
        logger.info("[ChromaVisualSync] updated count=%s", len(ids_out))
