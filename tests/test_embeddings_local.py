"""Embeddings locales (sentence-transformers), omitido si no hay dependencias."""

from __future__ import annotations

import pytest

pytest.importorskip("torch")
pytest.importorskip("sentence_transformers")

from aicos.config import EmbeddingsConfig, RuntimeConfig
from aicos.core.embeddings.factory import build_embedding_provider
from aicos.core.embeddings.local import LocalEmbeddingProvider


def test_local_provider_embed_and_batch() -> None:
    cfg = EmbeddingsConfig(
        provider="local",
        model="sentence-transformers/all-MiniLM-L6-v2",
        device="cpu",
        batch_size=4,
        normalize_embeddings=True,
    )
    p = LocalEmbeddingProvider(cfg)
    v = p.embed("hola mundo")
    assert len(v) == 384
    batch = p.embed_batch(["a", "b", "c"], batch_size=2)
    assert len(batch) == 3
    assert all(len(x) == 384 for x in batch)


def test_factory_openai_requires_key(monkeypatch) -> None:
    class _Cfg:
        embeddings = EmbeddingsConfig(provider="openai", model="text-embedding-3-small")
        runtime = RuntimeConfig(local_only=False, offline_mode=False, use_openai=True)

    monkeypatch.setattr("aicos.core.embeddings.factory.get_config", lambda *a, **k: _Cfg())
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("AICOS_OPENAI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="API key"):
        build_embedding_provider(api_key=None)
