"""Resolución de identificadores efectivos a partir de capas Chroma + SQLite."""

from __future__ import annotations

from aicos.application.cinematic_metadata.ports import CinematicMetadataReadPort
from aicos.domain.clip_usage.derivations import folder_fallback_hash_for_path
from aicos.domain.clip_usage.derivations import derive_visual_cluster_id as lexical_visual_cluster
from aicos.domain.cinematic_metadata.entities import SourceVideoMetadata
from aicos.domain.cinematic_metadata.rules import (
    resolve_source_video_identifier,
    resolve_visual_cluster_identifier,
)
from aicos.models.schemas import Recommendation


def _metadata_from_recommendation_chroma(rec: Recommendation) -> SourceVideoMetadata | None:
    sid = (rec.cm_source_video_id or "").strip()
    mid = (rec.cm_master_reel_id or "").strip()
    vcx = (rec.cm_cluster_explicit or "").strip()
    if not sid and not mid and not vcx:
        return None
    return SourceVideoMetadata(
        source_video_id=sid,
        master_reel_id=mid,
        visual_cluster_id_explicit=vcx,
    )


class CinematicMetadataResolver:
    """Orquesta precedencia: SQLite explícito > campos Chroma en Recommendation > heurística."""

    def __init__(self, store: CinematicMetadataReadPort | None = None) -> None:
        self._store = store

    def resolve_source_video_id(self, rec: Recommendation) -> str:
        folder_h = folder_fallback_hash_for_path(rec.clip_path or "", "")
        explicit_db: SourceVideoMetadata | None = None
        if self._store is not None:
            explicit_db = self._store.get_by_clip_id(rec.clip_id)
        explicit_chroma = _metadata_from_recommendation_chroma(rec)
        explicit = _merge_precedence(explicit_db, explicit_chroma)
        return resolve_source_video_identifier(explicit, folder_fallback_hash=folder_h)

    def resolve_visual_cluster_id(self, rec: Recommendation) -> str:
        explicit_db: SourceVideoMetadata | None = None
        if self._store is not None:
            explicit_db = self._store.get_by_clip_id(rec.clip_id)
        explicit_chroma = _metadata_from_recommendation_chroma(rec)
        explicit = _merge_precedence(explicit_db, explicit_chroma)
        lexical = lexical_visual_cluster(
            clip_id=rec.clip_id,
            subcategory=rec.clip_subcategory,
            context=rec.clip_context,
            semantic_text=rec.clip_semantic_text,
            absolute_path=rec.clip_path or "",
        )
        vfp = (rec.cm_visual_embedding_fp or "").strip() or None
        ec = (explicit.visual_cluster_id_explicit if explicit else None) or None
        return resolve_visual_cluster_identifier(
            explicit_cluster_id=ec,
            visual_embedding_fingerprint=vfp,
            lexical_cluster_id=lexical,
        )


def _merge_precedence(
    primary: SourceVideoMetadata | None,
    secondary: SourceVideoMetadata | None,
) -> SourceVideoMetadata | None:
    if primary is None:
        return secondary
    if secondary is None:
        return primary

    def pick(pa: str, pb: str) -> str:
        a = (pa or "").strip()
        if a:
            return a
        return (pb or "").strip()

    return SourceVideoMetadata(
        source_video_id=pick(primary.source_video_id, secondary.source_video_id),
        source_video_name=pick(primary.source_video_name, secondary.source_video_name),
        master_reel_id=pick(primary.master_reel_id, secondary.master_reel_id),
        shooting_session_id=pick(primary.shooting_session_id, secondary.shooting_session_id),
        camera_id=pick(primary.camera_id, secondary.camera_id),
        production_group=pick(primary.production_group, secondary.production_group),
        visual_collection=pick(primary.visual_collection, secondary.visual_collection),
        creation_date=pick(primary.creation_date, secondary.creation_date),
        location_tag=pick(primary.location_tag, secondary.location_tag),
        visual_cluster_id_explicit=pick(primary.visual_cluster_id_explicit, secondary.visual_cluster_id_explicit),
        provenance=primary.provenance,
    )
