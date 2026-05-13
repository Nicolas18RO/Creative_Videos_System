"""Dominio: metadatos cinematográficos explícitos (Fase 5, sin I/O ni ML)."""

from aicos.domain.cinematic_metadata.entities import SourceVideoMetadata, VisualEmbeddingSignature
from aicos.domain.cinematic_metadata.enums import CinematicMetadataProvenance
from aicos.domain.cinematic_metadata.rules import (
    fingerprint_visual_embedding,
    resolve_source_video_identifier,
    resolve_visual_cluster_identifier,
)

__all__ = [
    "CinematicMetadataProvenance",
    "SourceVideoMetadata",
    "VisualEmbeddingSignature",
    "fingerprint_visual_embedding",
    "resolve_source_video_identifier",
    "resolve_visual_cluster_identifier",
]
