"""Adaptador SQLite: huellas visuales + facetas para regeneración Chroma."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from aicos.application.multimodal_retrieval.ports import (
    MultimodalRegenWorkUnitBatchPort,
    VisualFingerprintReadPort,
)
from aicos.database.db import ClipCinematicMetadataRow, ClipRow, ClipVisualEmbeddingRow
from aicos.domain.multimodal_retrieval.entities import (
    ChromaClipFacet,
    MultimodalRegenWorkUnit,
    VisualFingerprintRecord,
)


def _parse_vec(raw: str) -> tuple[float, ...] | None:
    if not raw or not raw.strip():
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, list):
        return None
    out: list[float] = []
    for x in data:
        try:
            out.append(float(x))
        except (TypeError, ValueError):
            return None
    return tuple(out)


def _row_to_facet(clip: ClipRow, cm: ClipCinematicMetadataRow | None) -> ChromaClipFacet:
    return ChromaClipFacet(
        clip_id=clip.id,
        filename=clip.filename,
        relative_path=clip.relative_path,
        absolute_path=clip.absolute_path,
        gender=clip.gender,
        narrative_function=clip.narrative_function,
        subcategory=clip.subcategory,
        context=clip.context,
        semantic_text=clip.semantic_text,
        naming_compliant=bool(clip.naming_compliant),
        thumbnail_path=clip.thumbnail_path,
        source_video_id=cm.source_video_id if cm else None,
        source_video_name=cm.source_video_name if cm else None,
        master_reel_id=cm.master_reel_id if cm else None,
        shooting_session_id=cm.shooting_session_id if cm else None,
        camera_id=cm.camera_id if cm else None,
        production_group=cm.production_group if cm else None,
        visual_collection=cm.visual_collection if cm else None,
        creation_date=cm.creation_date if cm else None,
        location_tag=cm.location_tag if cm else None,
        visual_cluster_id_explicit=cm.visual_cluster_id_explicit if cm else None,
    )


def _to_visual(ve: ClipVisualEmbeddingRow, cm: ClipCinematicMetadataRow | None) -> VisualFingerprintRecord:
    src = (cm.source_video_id or "").strip() if cm else ""
    vcl = (cm.visual_cluster_id_explicit or "").strip() if cm else ""
    return VisualFingerprintRecord(
        clip_id=ve.clip_id,
        fingerprint=(ve.fingerprint or "").strip(),
        embedding_model=(ve.model_tag or "").strip(),
        embedding_dimension=int(ve.dimension),
        created_at=ve.created_at if isinstance(ve.created_at, datetime) else datetime.now(timezone.utc),
        source_video_id=src,
        visual_cluster_id=vcl,
    )


class SqliteVisualFingerprintReader(VisualFingerprintReadPort, MultimodalRegenWorkUnitBatchPort):
    """JOIN ``clip_visual_embeddings`` + ``clips`` + ``clip_cinematic_metadata``."""

    def fetch_work_units(
        self,
        session: Any,
        *,
        limit: int,
        after_clip_id: str | None,
    ) -> list[MultimodalRegenWorkUnit]:
        sess: Session = session
        stmt = (
            select(ClipVisualEmbeddingRow, ClipRow, ClipCinematicMetadataRow)
            .join(ClipRow, ClipRow.id == ClipVisualEmbeddingRow.clip_id)
            .outerjoin(ClipCinematicMetadataRow, ClipCinematicMetadataRow.clip_id == ClipVisualEmbeddingRow.clip_id)
            .where(ClipRow.asset_kind == "video")
            .order_by(ClipVisualEmbeddingRow.clip_id.asc())
            .limit(limit)
        )
        if after_clip_id:
            stmt = stmt.where(ClipVisualEmbeddingRow.clip_id > after_clip_id)
        out: list[MultimodalRegenWorkUnit] = []
        for ve, clip, cm in sess.execute(stmt).all():
            facet = _row_to_facet(clip, cm)
            visual = _to_visual(ve, cm)
            vec = _parse_vec(ve.embedding_json)
            out.append(MultimodalRegenWorkUnit(visual=visual, facet=facet, embedding_vector=vec))
        return out

    def fetch_batch(
        self,
        session: Any,
        *,
        limit: int,
        after_clip_id: str | None,
    ) -> list[VisualFingerprintRecord]:
        return [u.visual for u in self.fetch_work_units(session, limit=limit, after_clip_id=after_clip_id)]

    def fetch_by_clip_id(self, session: Any, clip_id: str) -> VisualFingerprintRecord | None:
        sess: Session = session
        stmt = (
            select(ClipVisualEmbeddingRow, ClipRow, ClipCinematicMetadataRow)
            .join(ClipRow, ClipRow.id == ClipVisualEmbeddingRow.clip_id)
            .outerjoin(ClipCinematicMetadataRow, ClipCinematicMetadataRow.clip_id == ClipVisualEmbeddingRow.clip_id)
            .where(ClipVisualEmbeddingRow.clip_id == clip_id)
            .limit(1)
        )
        row = sess.execute(stmt).first()
        if row is None:
            return None
        ve, clip, cm = row
        return _to_visual(ve, cm)
