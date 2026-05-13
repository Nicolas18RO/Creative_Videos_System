"""Entidades y objetos de valor para metadatos de producción y señal visual."""

from __future__ import annotations

from dataclasses import dataclass

from aicos.domain.cinematic_metadata.enums import CinematicMetadataProvenance


@dataclass(frozen=True, slots=True)
class SourceVideoMetadata:
    """Identidad explícita del video fuente (master / sesión / cámara).

    Los campos vacíos permiten persistencia parcial y fusión con heurísticas.
    """

    source_video_id: str = ""
    source_video_name: str = ""
    master_reel_id: str = ""
    shooting_session_id: str = ""
    camera_id: str = ""
    production_group: str = ""
    visual_collection: str = ""
    creation_date: str = ""
    location_tag: str = ""
    visual_cluster_id_explicit: str = ""
    provenance: CinematicMetadataProvenance = CinematicMetadataProvenance.EXPLICIT

    def has_explicit_source_key(self) -> bool:
        """True si hay un identificador de origen utilizable sin heurística de ruta."""
        if (self.source_video_id or "").strip():
            return True
        if (self.master_reel_id or "").strip():
            return True
        return False


@dataclass(frozen=True, slots=True)
class VisualEmbeddingSignature:
    """Referencia a embedding visual (no almacena tensores en dominio)."""

    fingerprint: str
    model_tag: str
    dimension: int
