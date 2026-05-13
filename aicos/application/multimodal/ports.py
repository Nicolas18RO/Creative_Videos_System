"""Puertos del batch OpenCLIP (sin SQLAlchemy en las firmas)."""

from __future__ import annotations

from typing import Any, Protocol

from aicos.domain.multimodal.entities import ClipVisualJobTarget, VisualEmbedding


class ClipVisualJobSourcePort(Protocol):
    """Iteración de clips vídeo candidatos para embedding visual."""

    def iter_targets(
        self,
        session: Any,
        *,
        limit: int,
        rescan_all: bool,
    ) -> list[ClipVisualJobTarget]:
        """Devuelve hasta ``limit`` clips pendientes (excluye ya indexados si aplica)."""


class KeyframeExportPort(Protocol):
    """Exporta un fotograma representativo a JPEG en disco."""

    def export_median_frame(
        self,
        *,
        video_path: str,
        output_jpeg_path: str,
        width: int,
        height: int,
    ) -> bool:
        """True si se generó el JPEG."""


class VisualEmbeddingBatchEncoderPort(Protocol):
    """Codificación batch de rutas de imagen → vectores normalizados."""

    def model_tag(self) -> str:
        """Identificador estable del modelo."""

    def encode_image_paths_batch(self, image_paths: list[str]) -> list[list[float] | None]:
        """Un vector por ruta (mismo orden); None si falla un ítem."""


class VisualEmbeddingPersistencePort(Protocol):
    """Persistencia de vectores y huellas (SQLite)."""

    def persist_visual_embedding(self, session: Any, embedding: VisualEmbedding) -> None:
        """Guarda embedding completo + huella asociada al clip."""


class ChromaVisualMetadataSyncPort(Protocol):
    """Sincroniza metadatos visuales en Chroma sin recalcular embeddings textuales."""

    def sync_clips(self, session: Any, clip_ids: list[str]) -> None:
        """Actualiza ``cm_*`` para los ids indicados."""
