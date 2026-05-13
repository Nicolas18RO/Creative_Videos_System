"""Entidades puras para regeneración multimodal en Chroma."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class VisualFingerprintRecord:
    """Huella visual persistida (SQLite) lista para validación y Chroma."""

    clip_id: str
    fingerprint: str
    embedding_model: str
    embedding_dimension: int
    created_at: datetime
    source_video_id: str
    visual_cluster_id: str


@dataclass(frozen=True, slots=True)
class ChromaFingerprintPayload:
    """Un upsert lógico hacia Chroma (embedding opcional según política de colección)."""

    chroma_id: str
    metadata: dict[str, str]
    embedding: tuple[float, ...] | None


@dataclass(frozen=True, slots=True)
class MultimodalIndexStats:
    """Métricas agregadas de una corrida de regeneración."""

    indexed: int
    skipped: int
    failed: int
    elapsed_ms: int
    processed: int = 0


@dataclass(frozen=True, slots=True)
class MultimodalContinuityHints:
    """Señales de continuidad para enriquecer metadatos (sin I/O)."""

    last_visual_fingerprint: str = ""
    last_visual_cluster_id: str = ""
    session_visual_style: str = ""


@dataclass(frozen=True, slots=True)
class MultimodalRegenWorkUnit:
    """Un clip listo para regenerar Chroma (dominio, sin ORM)."""

    visual: VisualFingerprintRecord
    facet: ChromaClipFacet
    embedding_vector: tuple[float, ...] | None


@dataclass(frozen=True, slots=True)
class ChromaClipFacet:
    """Facetas taxonómicas + cinematográficas serializables (sin ORM en aplicación)."""

    clip_id: str
    filename: str
    relative_path: str
    absolute_path: str
    gender: str | None
    narrative_function: str | None
    subcategory: str | None
    context: str | None
    semantic_text: str | None
    naming_compliant: bool
    thumbnail_path: str | None
    source_video_id: str | None
    source_video_name: str | None
    master_reel_id: str | None
    shooting_session_id: str | None
    camera_id: str | None
    production_group: str | None
    visual_collection: str | None
    creation_date: str | None
    location_tag: str | None
    visual_cluster_id_explicit: str | None
