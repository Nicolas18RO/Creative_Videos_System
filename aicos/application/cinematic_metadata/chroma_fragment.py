"""Fusión de metadatos explícitos con fragmentos indexables (Chroma, sin ORM)."""

from __future__ import annotations

from aicos.domain.cinematic_metadata.entities import SourceVideoMetadata
from aicos.domain.cinematic_metadata.rules import (
    fingerprint_visual_embedding,
    resolve_source_video_identifier,
    resolve_visual_cluster_identifier,
)


def chroma_cinematic_fragment(
    *,
    explicit: SourceVideoMetadata | None,
    folder_fallback_hash: str,
    lexical_visual_cluster_id: str,
    visual_embedding_vector: list[float] | None,
    embedding_model_tag: str = "",
    precomputed_visual_fp: str | None = None,
) -> dict[str, str]:
    """Claves string para Chroma (valores siempre str por compatibilidad con el índice actual)."""
    src = resolve_source_video_identifier(explicit, folder_fallback_hash=folder_fallback_hash)
    vfp = (precomputed_visual_fp or "").strip()
    if not vfp and visual_embedding_vector:
        vfp = fingerprint_visual_embedding(visual_embedding_vector, model_tag=embedding_model_tag)
    explicit_cluster = (explicit.visual_cluster_id_explicit if explicit else None) or None
    vcluster = resolve_visual_cluster_identifier(
        explicit_cluster_id=explicit_cluster,
        visual_embedding_fingerprint=vfp or None,
        lexical_cluster_id=lexical_visual_cluster_id,
    )
    return _build_keys(
        source_id=src,
        visual_cluster=vcluster,
        explicit=explicit,
        visual_fp=vfp,
        model_tag=embedding_model_tag,
    )


def _build_keys(
    *,
    source_id: str,
    visual_cluster: str,
    explicit: SourceVideoMetadata | None,
    visual_fp: str,
    model_tag: str,
) -> dict[str, str]:
    out: dict[str, str] = {
        "cm_source_video_id": source_id[:128],
        "cm_visual_cluster_id": visual_cluster[:128],
        "cm_visual_embedding_fp": (visual_fp or "")[:64],
        "cm_embedding_model": (model_tag or "")[:64],
    }
    if explicit is not None:
        out["cm_source_video_name"] = (explicit.source_video_name or "")[:256]
        out["cm_master_reel_id"] = (explicit.master_reel_id or "")[:128]
        out["cm_shooting_session_id"] = (explicit.shooting_session_id or "")[:128]
        out["cm_camera_id"] = (explicit.camera_id or "")[:64]
        out["cm_production_group"] = (explicit.production_group or "")[:128]
        out["cm_visual_collection"] = (explicit.visual_collection or "")[:128]
        out["cm_creation_date"] = (explicit.creation_date or "")[:32]
        out["cm_location_tag"] = (explicit.location_tag or "")[:128]
        out["cm_cluster_explicit"] = (explicit.visual_cluster_id_explicit or "")[:128]
        out["cm_provenance"] = explicit.provenance.value
    return out
