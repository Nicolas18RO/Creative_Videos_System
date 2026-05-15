"""Infraestructura Fase 6.4 — índice vectorial de estilo editorial."""

from aicos.infrastructure.editorial_style_retrieval.chroma_editorial_style_index import (
    ChromaEditorialStyleIndexAdapter,
)
from aicos.infrastructure.editorial_style_retrieval.null_editorial_style_index import (
    NullEditorialStyleVectorIndex,
)

__all__ = ["ChromaEditorialStyleIndexAdapter", "NullEditorialStyleVectorIndex"]
