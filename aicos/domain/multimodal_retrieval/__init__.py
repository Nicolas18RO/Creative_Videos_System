"""Dominio: regeneración de fingerprints en Chroma y señales híbridas (Fase 5.2)."""

from aicos.domain.multimodal_retrieval.entities import (
    ChromaClipFacet,
    ChromaFingerprintPayload,
    MultimodalContinuityHints,
    MultimodalIndexStats,
    MultimodalRegenWorkUnit,
    VisualFingerprintRecord,
)
from aicos.domain.multimodal_retrieval.hybrid_scoring import (
    compute_hybrid_final_score,
    compute_visual_similarity_components,
)

__all__ = [
    "ChromaClipFacet",
    "ChromaFingerprintPayload",
    "MultimodalRegenWorkUnit",
    "MultimodalContinuityHints",
    "MultimodalIndexStats",
    "VisualFingerprintRecord",
    "compute_hybrid_final_score",
    "compute_visual_similarity_components",
]
