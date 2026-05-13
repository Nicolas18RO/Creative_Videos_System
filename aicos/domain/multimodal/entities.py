"""Entidades de embedding visual y resultados de ítem batch."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from aicos.domain.multimodal.enums import BatchItemStatus


@dataclass(frozen=True, slots=True)
class ClipVisualJobTarget:
    """Identificador mínimo para procesar un clip en el batch."""

    clip_id: str
    absolute_path: str


@dataclass(frozen=True, slots=True)
class VisualEmbedding:
    """Embedding visual normalizado asociado a un clip (dominio, sin tensores externos)."""

    clip_id: str
    embedding_vector: tuple[float, ...]
    embedding_model: str
    embedding_dimension: int
    created_at: datetime
    visual_fingerprint: str = ""

    def __post_init__(self) -> None:
        if len(self.embedding_vector) != self.embedding_dimension:
            raise ValueError("embedding_dimension debe coincidir con len(embedding_vector)")


@dataclass(frozen=True, slots=True)
class BatchClipVisualResult:
    """Resultado del procesamiento de un clip en el batch."""

    clip_id: str
    status: BatchItemStatus
    message: str = ""
    fingerprint: str = ""
    embedding_dimension: int = 0
