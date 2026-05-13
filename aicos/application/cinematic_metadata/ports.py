"""Puertos (Protocol): lectura de metadatos y codificación visual (sin SQLAlchemy aquí)."""

from __future__ import annotations

from typing import Protocol, Sequence

from aicos.domain.cinematic_metadata.entities import SourceVideoMetadata


class CinematicMetadataReadPort(Protocol):
    """Lectura de metadatos explícitos por clip."""

    def get_by_clip_id(self, clip_id: str) -> SourceVideoMetadata | None:
        """Devuelve metadatos de producción o None si no hay fila."""

    def get_many_by_clip_ids(self, clip_ids: Sequence[str]) -> dict[str, SourceVideoMetadata]:
        """Carga en lote para indexación y pipelines batch."""


class VisualFrameEmbeddingPort(Protocol):
    """Codificación de un fotograma/archivo de imagen en vector (implementación infra)."""

    def model_tag(self) -> str:
        """Etiqueta estable del modelo (p. ej. ``openclip/ViT-B-32``)."""

    def encode_image_path(self, image_path: str) -> list[float] | None:
        """Vector de embedding o None si no disponible."""
