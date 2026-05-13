"""Construcción de metadatos Chroma por clip (SQLite + reglas Fase 5)."""

from __future__ import annotations

from aicos.application.cinematic_metadata.chroma_fragment import chroma_cinematic_fragment
from aicos.database.db import ClipCinematicMetadataRow, ClipRow
from aicos.domain.clip_usage.derivations import derive_visual_cluster_id, folder_fallback_hash_for_path
from aicos.services.cinematic_metadata_mapping import clip_cinematic_row_to_domain


def build_chroma_metadata_bundle(row: ClipRow, cm_row: ClipCinematicMetadataRow | None) -> dict:
    """Metadatos base de taxonomía + fragmento cinematográfico canónico."""
    sem = row.semantic_text or ""
    base = {
        "gender": row.gender or "",
        "narrative_function": row.narrative_function or "",
        "subcategory": row.subcategory or "",
        "context": row.context or "",
        "absolute_path": row.absolute_path,
        "relative_path": row.relative_path,
        "semantic_text": sem[:2000],
        "naming_compliant": "1" if row.naming_compliant else "0",
        "variants_in_subcategory": "0",
        "thumbnail_path": row.thumbnail_path or "",
    }
    explicit = clip_cinematic_row_to_domain(cm_row)
    lexical = derive_visual_cluster_id(
        clip_id=row.id,
        subcategory=row.subcategory,
        context=row.context,
        semantic_text=row.semantic_text,
        absolute_path=row.absolute_path,
    )
    folder_h = folder_fallback_hash_for_path(row.absolute_path, row.relative_path)
    pre_fp = (cm_row.visual_embedding_fingerprint or None) if cm_row else None
    base.update(
        chroma_cinematic_fragment(
            explicit=explicit,
            folder_fallback_hash=folder_h,
            lexical_visual_cluster_id=lexical,
            visual_embedding_vector=None,
            embedding_model_tag="",
            precomputed_visual_fp=pre_fp,
        )
    )
    return base
