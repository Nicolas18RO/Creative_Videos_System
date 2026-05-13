"""Abstracción ChromaDB persistente para la colección de clips."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Sequence

import chromadb
from chromadb.api.models.Collection import Collection

from aicos.config import get_config

logger = logging.getLogger(__name__)

_DEFAULT_COLLECTION = "clips_v1"


def get_clip_collection_name() -> str:
    """Nombre de colección Chroma (permite separar dimensiones al cambiar de modelo)."""
    raw = get_config().embeddings.collection_name
    name = (raw or _DEFAULT_COLLECTION).strip()
    return name or _DEFAULT_COLLECTION


class VectorStore:
    """Almacén vectorial local."""

    def __init__(self, persist_path: Path | None = None) -> None:
        paths = get_config().resolved_paths()
        self._path = persist_path or paths["vector_store"]
        self._path.mkdir(parents=True, exist_ok=True)
        self._collection_name = get_clip_collection_name()
        self._client = chromadb.PersistentClient(path=str(self._path))
        self._collection: Collection = self._client.get_or_create_collection(
            name=self._collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.debug("Chroma colección=%s path=%s", self._collection_name, self._path)

    @property
    def collection_name(self) -> str:
        return self._collection_name

    @property
    def collection(self) -> Collection:
        return self._collection

    def upsert_clips(
        self,
        ids: Sequence[str],
        embeddings: Sequence[Sequence[float]],
        documents: Sequence[str],
        metadatas: Sequence[dict[str, Any]],
    ) -> None:
        """Inserta o actualiza vectores de clips."""
        self._collection.upsert(
            ids=list(ids),
            embeddings=[list(map(float, e)) for e in embeddings],
            documents=list(documents),
            metadatas=list(metadatas),
        )

    def get_clip_payloads(self, ids: Sequence[str]) -> dict[str, dict[str, Any]]:
        """Devuelve por id: ``metadata``, ``document``, ``embedding`` (si existen en Chroma)."""
        raw = list(ids)
        if not raw:
            return {}
        res = self._collection.get(ids=raw, include=["metadatas", "documents", "embeddings"])
        out: dict[str, dict[str, Any]] = {}
        id_list = res.get("ids") or []
        metas = res.get("metadatas") or []
        docs = res.get("documents") or []
        embs = res.get("embeddings") or []
        for i, cid in enumerate(id_list):
            out[str(cid)] = {
                "metadata": metas[i] if i < len(metas) and metas[i] is not None else {},
                "document": docs[i] if i < len(docs) else "",
                "embedding": embs[i] if i < len(embs) else None,
            }
        return out

    def update_clip_documents_metadatas(
        self,
        *,
        ids: Sequence[str],
        documents: Sequence[str] | None = None,
        embeddings: Sequence[Sequence[float]] | None = None,
        metadatas: Sequence[dict[str, Any]] | None = None,
    ) -> None:
        """Actualiza subset de campos (Chroma ``update``); preserva lo no enviado según backend."""
        kwargs: dict[str, Any] = {"ids": list(ids)}
        if documents is not None:
            kwargs["documents"] = list(documents)
        if embeddings is not None:
            kwargs["embeddings"] = [list(map(float, e)) for e in embeddings]
        if metadatas is not None:
            kwargs["metadatas"] = list(metadatas)
        self._collection.update(**kwargs)

    def delete_all(self) -> None:
        """Borra la colección y la recrea (reindex completo)."""
        try:
            self._client.delete_collection(self._collection_name)
        except Exception as e:
            logger.warning("No se pudo borrar la colección %s: %s", self._collection_name, e)
        self._collection = self._client.get_or_create_collection(
            name=self._collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def query(
        self,
        embedding: Sequence[float],
        n_results: int = 15,
        where: dict[str, Any] | None = None,
    ) -> tuple[list[str], list[float], list[dict[str, Any]]]:
        """Consulta por similitud coseno; retorna ids, similitud aproximada y metadatos.

        Args:
            where: Filtro de metadatos Chroma (p. ej. ``{"narrative_function": "HOOK"}``).
        """
        kwargs: dict[str, Any] = {
            "query_embeddings": [list(map(float, embedding))],
            "n_results": n_results,
            "include": ["distances", "metadatas"],
        }
        if where:
            kwargs["where"] = where
        res = self._collection.query(**kwargs)
        ids = (res.get("ids") or [[]])[0]
        distances = (res.get("distances") or [[]])[0]
        metas = (res.get("metadatas") or [[]])[0]
        sims: list[float] = []
        for d in distances:
            try:
                sims.append(max(0.0, min(1.0, 1.0 - float(d))))
            except (TypeError, ValueError):
                sims.append(0.0)
        return list(ids), sims, list(metas)
