"""Tests Fase 6.4 — recuperación por similitud de estilo editorial."""

from __future__ import annotations

from unittest.mock import MagicMock

from aicos.application.editorial_style_retrieval.editorial_style_retrieval_service import EditorialStyleRetrievalService
from aicos.config import EditorialStyleRetrievalConfig
from aicos.domain.editorial_style_embedding.entities import EditorialStyleEmbedding
from aicos.domain.editorial_style_retrieval.scoring import hybrid_similarity_score


def _unit_axis(dim: int, index: int) -> tuple[float, ...]:
    return tuple(1.0 if i == index else 0.0 for i in range(dim))


def _emb(
    cid: str,
    *,
    structural_axis: int = 0,
    semantic_axis: int | None = None,
    dim: int = 128,
) -> EditorialStyleEmbedding:
    sv = _unit_axis(dim, structural_axis)
    sem = _unit_axis(dim, semantic_axis) if semantic_axis is not None else None
    return EditorialStyleEmbedding(
        creative_id=cid,
        structural_vector=sv,
        semantic_vector=sem,
        fused_vector=sv,
        digest_text=f"d:{cid}",
        digest_sha256="a" * 64,
        structural_model_tag="t",
        semantic_model_tag="m" if sem else None,
        fusion_mode="test",
    )


class _FakeIndex:
    def __init__(self) -> None:
        self._vecs: dict[str, tuple[float, ...]] = {}

    def upsert_structural(
        self,
        *,
        creative_id: str,
        structural_vector: tuple[float, ...],
        digest_text: str,
        metadata: dict,
    ) -> None:
        self._vecs[creative_id] = structural_vector

    def delete_creative(self, creative_id: str) -> None:
        self._vecs.pop(creative_id, None)

    def query_structural(
        self,
        *,
        query_vector: tuple[float, ...],
        n_results: int,
        exclude_creative_ids: frozenset[str] | None,
    ) -> list[tuple[str, float, dict[str, str]]]:
        from aicos.domain.editorial_style_retrieval.scoring import cosine_similarity

        ex = exclude_creative_ids or frozenset()
        ranked: list[tuple[str, float]] = []
        for cid, vec in self._vecs.items():
            if cid in ex:
                continue
            ranked.append((cid, cosine_similarity(query_vector, vec)))
        ranked.sort(key=lambda x: x[1], reverse=True)
        return [(cid, sim, {}) for cid, sim in ranked[:n_results]]


class _FakeRead:
    def __init__(self, store: dict[str, EditorialStyleEmbedding]) -> None:
        self._store = store

    def get_many_by_creative_ids(self, session, creative_ids):  # noqa: ARG002
        return {k: self._store[k] for k in creative_ids if k in self._store}


def test_retrieval_disabled_returns_empty() -> None:
    cfg = EditorialStyleRetrievalConfig(enabled=False)
    svc = EditorialStyleRetrievalService(cfg=cfg, index=_FakeIndex(), embedding_read=_FakeRead({}))
    res = svc.retrieve_similar(MagicMock(), anchor_creative_id="x", top_k=5)
    assert res.hits == ()


def test_retrieval_anchor_missing() -> None:
    cfg = EditorialStyleRetrievalConfig(enabled=True, rerank_pool_size=10)
    svc = EditorialStyleRetrievalService(cfg=cfg, index=_FakeIndex(), embedding_read=_FakeRead({}))
    res = svc.retrieve_similar(MagicMock(), anchor_creative_id="missing", top_k=3)
    assert res.hits == ()


def test_retrieval_structural_ranking() -> None:
    store = {
        "a": _emb("a", structural_axis=0),
        "b": _emb("b", structural_axis=0),
        "c": _emb("c", structural_axis=5),
    }
    idx = _FakeIndex()
    for e in store.values():
        idx.upsert_structural(
            creative_id=e.creative_id,
            structural_vector=e.structural_vector,
            digest_text=e.digest_text,
            metadata={},
        )
    cfg = EditorialStyleRetrievalConfig(enabled=True, rerank_pool_size=10, enable_semantic_rerank=False)
    svc = EditorialStyleRetrievalService(cfg=cfg, index=idx, embedding_read=_FakeRead(store))
    res = svc.retrieve_similar(MagicMock(), anchor_creative_id="a", top_k=2, exclude_self=True)
    ids = [h.creative_id for h in res.hits]
    assert "b" in ids and "c" in ids
    assert res.hits[0].creative_id == "b"
    assert res.hits[0].structural_similarity >= res.hits[1].structural_similarity


def test_retrieval_semantic_rerank_changes_order() -> None:
    store = {
        "a": _emb("a", structural_axis=0, semantic_axis=0),
        "b": _emb("b", structural_axis=0, semantic_axis=0),
        "c": _emb("c", structural_axis=0, semantic_axis=3),
    }
    raw_order = [
        ("c", 0.6, {}),
        ("b", 0.5, {}),
    ]

    class _FixedRawIndex:
        def upsert_structural(self, **kwargs: object) -> None:
            return

        def delete_creative(self, creative_id: str) -> None:
            return

        def query_structural(self, **kwargs: object) -> list[tuple[str, float, dict]]:
            return list(raw_order)

    cfg = EditorialStyleRetrievalConfig(
        enabled=True,
        rerank_pool_size=10,
        enable_semantic_rerank=True,
        hybrid_weight_structural=0.65,
        hybrid_weight_semantic=0.35,
    )
    svc = EditorialStyleRetrievalService(cfg=cfg, index=_FixedRawIndex(), embedding_read=_FakeRead(store))
    res = svc.retrieve_similar(MagicMock(), anchor_creative_id="a", top_k=2, exclude_self=True)
    assert res.used_semantic_hybrid is True
    assert [h.creative_id for h in res.hits] == ["b", "c"]


def test_hybrid_similarity_score_semantic_none() -> None:
    s = hybrid_similarity_score(0.8, None, weight_structural=0.5, weight_semantic=0.5)
    assert abs(s - 0.8) < 1e-9
