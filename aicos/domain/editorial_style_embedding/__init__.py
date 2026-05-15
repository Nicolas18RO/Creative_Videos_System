"""Dominio: embeddings de estilo editorial (Fase 6.3)."""

from aicos.domain.editorial_style_embedding.digest_builder import (
    build_editorial_style_digest_text,
    sha256_hex,
    summarize_patterns_for_digest,
)
from aicos.domain.editorial_style_embedding.entities import EditorialStyleEmbedding, StyleStructuralSource
from aicos.domain.editorial_style_embedding.structural_vector import structural_vector_from_source

__all__ = [
    "EditorialStyleEmbedding",
    "StyleStructuralSource",
    "build_editorial_style_digest_text",
    "sha256_hex",
    "structural_vector_from_source",
    "summarize_patterns_for_digest",
]
