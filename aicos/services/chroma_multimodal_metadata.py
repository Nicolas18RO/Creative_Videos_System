"""Fusión de metadatos Chroma: textual + cinematográfico + huella visual + continuidad (Fase 5.2)."""

from __future__ import annotations

import logging

from aicos.database.db import ClipCinematicMetadataRow, ClipRow
from aicos.domain.multimodal_retrieval.entities import (
    ChromaClipFacet,
    MultimodalContinuityHints,
    VisualFingerprintRecord,
)
from aicos.services.chroma_clip_metadata import build_chroma_metadata_bundle

logger = logging.getLogger(__name__)


def _facet_to_clip_row(facet: ChromaClipFacet) -> ClipRow:
    """Construye fila ORM transitoria solo para reutilizar ``build_chroma_metadata_bundle``."""
    r = ClipRow()
    r.id = facet.clip_id
    r.filename = facet.filename
    r.relative_path = facet.relative_path
    r.absolute_path = facet.absolute_path
    r.gender = facet.gender
    r.narrative_function = facet.narrative_function
    r.subcategory = facet.subcategory
    r.context = facet.context
    r.semantic_text = facet.semantic_text
    r.naming_compliant = facet.naming_compliant
    r.thumbnail_path = facet.thumbnail_path
    return r


def _facet_to_cm_row(facet: ChromaClipFacet, visual: VisualFingerprintRecord) -> ClipCinematicMetadataRow:
    """Fila cinematográfica con huella visual actualizada desde Phase 5.1."""
    cm = ClipCinematicMetadataRow()
    cm.clip_id = facet.clip_id
    cm.source_video_id = facet.source_video_id
    cm.source_video_name = facet.source_video_name
    cm.master_reel_id = facet.master_reel_id
    cm.shooting_session_id = facet.shooting_session_id
    cm.camera_id = facet.camera_id
    cm.production_group = facet.production_group
    cm.visual_collection = facet.visual_collection
    cm.creation_date = facet.creation_date
    cm.location_tag = facet.location_tag
    cm.visual_cluster_id_explicit = facet.visual_cluster_id_explicit
    cm.visual_embedding_fingerprint = (visual.fingerprint or "").strip() or None
    cm.provenance = "explicit"
    return cm


def build_multimodal_chroma_metadata(
    *,
    facet: ChromaClipFacet,
    visual: VisualFingerprintRecord,
    continuity: MultimodalContinuityHints | None = None,
    regenerate: bool = True,
) -> dict[str, str]:
    """Combina taxonomía, metadatos cinematográficos y señales de continuidad para Chroma.

    Args:
        facet: facetas persistidas en SQLite (clips + cinematic).
        visual: registro de embedding visual (huella y modelo).
        continuity: pistas opcionales de sesión (continuidad visual).
        regenerate: si false, solo devuelve bundle base (compatibilidad; mismo coste actual).

    Returns:
        Diccionario plano ``str -> str`` listo para Chroma.
    """
    if not regenerate:
        logger.debug("[MultimodalMetadata] regenerate=false clip=%s (bundle completo igual)", facet.clip_id)
    row = _facet_to_clip_row(facet)
    cm_row = _facet_to_cm_row(facet, visual)
    base = build_chroma_metadata_bundle(row, cm_row)
    base["cm_embedding_model"] = (visual.embedding_model or "")[:64]
    base["cm_visual_embedding_dim"] = str(int(visual.embedding_dimension))
    if continuity is not None:
        if continuity.last_visual_fingerprint.strip():
            base["cm_continuity_prev_fp"] = continuity.last_visual_fingerprint.strip()[:64]
        if continuity.last_visual_cluster_id.strip():
            base["cm_continuity_prev_cluster"] = continuity.last_visual_cluster_id.strip()[:128]
        if continuity.session_visual_style.strip():
            base["cm_continuity_style"] = continuity.session_visual_style.strip()[:64]
    return base
