"""Construcción de registros de sesión para inteligencia de uso (sin I/O)."""

from __future__ import annotations

import time

from aicos.application.cinematic_metadata.resolver import CinematicMetadataResolver
from aicos.models.schemas import ClipUsageRecordSchema, Recommendation


def _clip_blob(r: Recommendation) -> str:
    parts = [
        r.clip_semantic_text or "",
        r.clip_subcategory or "",
        r.clip_context or "",
        r.clip_path or "",
        r.narrative_function or "",
    ]
    return " ".join(parts).lower()


def build_usage_record_schema(*, scene_index: int, rec: Recommendation) -> ClipUsageRecordSchema:
    """Crea el registro serializable que alimenta penalizaciones en escenas posteriores."""
    fp = _clip_blob(rec)[:480]
    resolver = CinematicMetadataResolver(None)
    return ClipUsageRecordSchema(
        clip_id=rec.clip_id,
        source_video_id=resolver.resolve_source_video_id(rec),
        visual_cluster_id=resolver.resolve_visual_cluster_id(rec),
        scene_index=scene_index,
        timestamp=time.time(),
        usage_type="selection",
        clip_fingerprint=fp,
    )
