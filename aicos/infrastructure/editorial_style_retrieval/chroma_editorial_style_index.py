"""Adaptador Chroma para vectores estructurales 128-d de estilo editorial (Fase 6.4)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import chromadb
from chromadb.api.models.Collection import Collection

from aicos.config import EditorialStyleRetrievalConfig, get_config

logger = logging.getLogger(__name__)


def _flatten_metadata(meta: dict[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    for k, v in meta.items():
        if v is None:
            continue
        out[str(k)] = str(v)
    return out


class ChromaEditorialStyleIndexAdapter:
    """Colección dedicada (cosine) separada de la de clips multimodal."""

    def __init__(self, cfg: EditorialStyleRetrievalConfig | None = None) -> None:
        self._cfg = cfg or get_config().editorial_style_retrieval
        paths = get_config().resolved_paths()
        self._path: Path = paths["vector_store"]
        self._path.mkdir(parents=True, exist_ok=True)
        name = (self._cfg.collection_name or "editorial_style_structural_v1").strip()
        self._collection_name = name or "editorial_style_structural_v1"
        self._client = chromadb.PersistentClient(path=str(self._path))
        self._collection: Collection = self._client.get_or_create_collection(
            name=self._collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.debug(
            "Chroma editorial style index collection=%s path=%s",
            self._collection_name,
            self._path,
        )

    def upsert_structural(
        self,
        *,
        creative_id: str,
        structural_vector: tuple[float, ...],
        digest_text: str,
        metadata: dict[str, Any],
    ) -> None:
        flat = _flatten_metadata(metadata)
        self._collection.upsert(
            ids=[creative_id],
            embeddings=[list(map(float, structural_vector))],
            documents=[digest_text or ""],
            metadatas=[flat],
        )

    def delete_creative(self, creative_id: str) -> None:
        try:
            self._collection.delete(ids=[creative_id])
        except Exception:
            logger.debug("[StyleRetrievalIndex] delete miss creative_id=%s", creative_id)

    def query_structural(
        self,
        *,
        query_vector: tuple[float, ...],
        n_results: int,
        exclude_creative_ids: frozenset[str] | None,
    ) -> list[tuple[str, float, dict[str, Any]]]:
        exclude = exclude_creative_ids or frozenset()
        extra = len(exclude) + 8
        fetch_n = min(512, max(n_results + extra, n_results))
        res = self._collection.query(
            query_embeddings=[list(map(float, query_vector))],
            n_results=fetch_n,
            include=["distances", "metadatas"],
        )
        ids = (res.get("ids") or [[]])[0]
        distances = (res.get("distances") or [[]])[0]
        metas = (res.get("metadatas") or [[]])[0]
        out: list[tuple[str, float, dict[str, Any]]] = []
        for i, cid in enumerate(ids):
            if cid in exclude:
                continue
            d = distances[i] if i < len(distances) else 1.0
            try:
                sim = max(0.0, min(1.0, 1.0 - float(d)))
            except (TypeError, ValueError):
                sim = 0.0
            meta = metas[i] if i < len(metas) and metas[i] is not None else {}
            out.append((str(cid), sim, dict(meta)))
            if len(out) >= n_results:
                break
        return out
