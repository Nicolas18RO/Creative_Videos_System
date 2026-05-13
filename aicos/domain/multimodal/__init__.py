"""Dominio multimodal: embeddings visuales y resultados de jobs batch (sin torch/Chroma)."""

from aicos.domain.multimodal.entities import BatchClipVisualResult, ClipVisualJobTarget, VisualEmbedding
from aicos.domain.multimodal.enums import BatchItemStatus, MultimodalBatchPhase
from aicos.domain.multimodal.rules import visual_fingerprint_from_vector

__all__ = [
    "BatchClipVisualResult",
    "BatchItemStatus",
    "MultimodalBatchPhase",
    "VisualEmbedding",
    "visual_fingerprint_from_vector",
]
