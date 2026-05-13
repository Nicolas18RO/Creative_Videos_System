"""Repositorio SQLite: metadata editorial (Fase 5.3)."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from aicos.application.editorial_metadata.ports import (
    EditorialMetadataReadPort,
    EditorialMetadataWritePort,
)
from aicos.database.db import (
    ClipCinematicMetadataRow,
    ClipRow,
    EditorialMetadataRow,
)
from aicos.domain.clip_usage.derivations import derive_visual_cluster_id
from aicos.domain.editorial_metadata.entities import EditorialMetadataRecord
from aicos.domain.editorial_metadata.rules import apply_editorial_override, normalize_editorial_tags

logger = logging.getLogger(__name__)

_MAX_CORRECTIONS = 50


def _to_domain(
    clip: ClipRow,
    cm: ClipCinematicMetadataRow | None,
    em: EditorialMetadataRow | None,
) -> EditorialMetadataRecord:
    lex = derive_visual_cluster_id(
        clip_id=clip.id,
        subcategory=clip.subcategory,
        context=clip.context,
        semantic_text=clip.semantic_text,
        absolute_path=clip.absolute_path,
    )
    explicit_cluster = (cm.visual_cluster_id_explicit or "").strip() if cm else ""
    auto_cluster = explicit_cluster or lex
    override = (em.visual_cluster_override.strip() if em and em.visual_cluster_override else None)
    resolved = apply_editorial_override(auto_cluster=auto_cluster, cluster_override=override)
    src = ""
    if em and (em.editorial_source_video_id or "").strip():
        src = (em.editorial_source_video_id or "").strip()
    elif cm and cm.source_video_id:
        src = (cm.source_video_id or "").strip()
    master = ""
    if em and (em.editorial_master_reel_id or "").strip():
        master = (em.editorial_master_reel_id or "").strip()
    elif cm and cm.master_reel_id:
        master = (cm.master_reel_id or "").strip()
    e = em
    return EditorialMetadataRecord(
        clip_id=clip.id,
        source_video_id=src[:128],
        master_reel_id=master[:128],
        editorial_tags=(e.editorial_tags if e else "") or "",
        editorial_notes=(e.editorial_notes if e else "") or "",
        narrative_role=(e.narrative_role if e else "") or "",
        emotion_profile=(e.emotion_profile if e else "") or "",
        visual_style=(e.visual_style if e else "") or "",
        cinematic_style=(e.cinematic_style if e else "") or "",
        visual_cluster_id=resolved[:128],
        cluster_override=(e.visual_cluster_override or "") if e else "",
        pacing_type=(e.pacing_type if e else "") or "",
        shot_type=(e.shot_type if e else "") or "",
        quality_score=e.quality_score if e else None,
        cinematic_score=e.cinematic_score if e else None,
        reviewed=bool(e.reviewed) if e else False,
        reviewed_by=(e.reviewed_by or "") if e else "",
        reviewed_at=e.reviewed_at if e else None,
        created_at=e.created_at if e else None,
        updated_at=e.updated_at if e else None,
    )


class SqlEditorialMetadataRepository(EditorialMetadataReadPort, EditorialMetadataWritePort):
    """JOIN ``clips`` + ``clip_cinematic_metadata`` + ``editorial_metadata``."""

    def get_by_clip_id(self, session: Any, clip_id: str) -> EditorialMetadataRecord | None:
        sess: Session = session
        clip = sess.get(ClipRow, clip_id)
        if clip is None:
            return None
        cm = sess.get(ClipCinematicMetadataRow, clip_id)
        em = sess.get(EditorialMetadataRow, clip_id)
        return _to_domain(clip, cm, em)

    def list_paginated(self, session: Any, *, offset: int, limit: int) -> list[EditorialMetadataRecord]:
        sess: Session = session
        stmt = (
            select(ClipRow, ClipCinematicMetadataRow, EditorialMetadataRow)
            .outerjoin(ClipCinematicMetadataRow, ClipCinematicMetadataRow.clip_id == ClipRow.id)
            .outerjoin(EditorialMetadataRow, EditorialMetadataRow.clip_id == ClipRow.id)
            .where(ClipRow.asset_kind == "video")
            .order_by(ClipRow.id.asc())
            .offset(offset)
            .limit(limit)
        )
        out: list[EditorialMetadataRecord] = []
        for clip, cm, em in sess.execute(stmt).all():
            out.append(_to_domain(clip, cm, em))
        return out

    def search_by_tags(self, session: Any, *, tag_query: str, limit: int) -> list[EditorialMetadataRecord]:
        sess: Session = session
        tokens = [t for t in normalize_editorial_tags(tag_query).split(",") if t]
        if not tokens:
            return []
        conds = []
        for t in tokens:
            conds.append(func.lower(EditorialMetadataRow.editorial_tags).contains(t))
        stmt = (
            select(ClipRow, ClipCinematicMetadataRow, EditorialMetadataRow)
            .join(EditorialMetadataRow, EditorialMetadataRow.clip_id == ClipRow.id)
            .outerjoin(ClipCinematicMetadataRow, ClipCinematicMetadataRow.clip_id == ClipRow.id)
            .where(ClipRow.asset_kind == "video", or_(*conds))
            .order_by(ClipRow.id.asc())
            .limit(limit)
        )
        out: list[EditorialMetadataRecord] = []
        for clip, cm, em in sess.execute(stmt).all():
            if em is None:
                continue
            out.append(_to_domain(clip, cm, em))
        return out

    def search_by_cluster(self, session: Any, *, cluster_id: str, limit: int, offset: int) -> list[EditorialMetadataRecord]:
        sess: Session = session
        cid = cluster_id.strip()
        stmt = (
            select(ClipRow, ClipCinematicMetadataRow, EditorialMetadataRow)
            .outerjoin(ClipCinematicMetadataRow, ClipCinematicMetadataRow.clip_id == ClipRow.id)
            .outerjoin(EditorialMetadataRow, EditorialMetadataRow.clip_id == ClipRow.id)
            .where(
                ClipRow.asset_kind == "video",
                or_(
                    EditorialMetadataRow.visual_cluster_override == cid,
                    ClipCinematicMetadataRow.visual_cluster_id_explicit == cid,
                ),
            )
            .order_by(ClipRow.id.asc())
            .offset(offset)
            .limit(limit)
        )
        out: list[EditorialMetadataRecord] = []
        for clip, cm, em in sess.execute(stmt).all():
            out.append(_to_domain(clip, cm, em))
        return out

    def fetch_editorial_rank_facets(
        self, session: Any, clip_ids: list[str]
    ) -> dict[str, tuple[float | None, float | None, str | None, str | None]]:
        if not clip_ids:
            return {}
        sess: Session = session
        stmt = select(EditorialMetadataRow).where(EditorialMetadataRow.clip_id.in_(clip_ids))
        rows = sess.execute(stmt).scalars().all()
        out: dict[str, tuple[float | None, float | None, str | None, str | None]] = {}
        for r in rows:
            out[r.clip_id] = (
                r.quality_score,
                r.cinematic_score,
                (r.visual_cluster_override or None),
                (r.editorial_tags or None),
            )
        return out

    def save(self, session: Any, record: EditorialMetadataRecord) -> None:
        sess: Session = session
        row = sess.get(EditorialMetadataRow, record.clip_id)
        is_new = row is None
        if is_new:
            row = EditorialMetadataRow(clip_id=record.clip_id)
        row.editorial_tags = normalize_editorial_tags(record.editorial_tags)
        row.editorial_notes = record.editorial_notes or ""
        row.visual_cluster_override = record.cluster_override or None
        row.narrative_role = record.narrative_role or None
        row.emotion_profile = record.emotion_profile or None
        row.visual_style = record.visual_style or None
        row.cinematic_style = record.cinematic_style or None
        row.pacing_type = record.pacing_type or None
        row.shot_type = record.shot_type or None
        row.editorial_source_video_id = record.source_video_id or None
        row.editorial_master_reel_id = record.master_reel_id or None
        row.quality_score = record.quality_score
        row.cinematic_score = record.cinematic_score
        row.reviewed = record.reviewed
        row.reviewed_by = record.reviewed_by or None
        row.reviewed_at = record.reviewed_at
        if is_new:
            sess.add(row)
        logger.debug("[EditorialMetadata] save clip_id=%s", record.clip_id)

    def patch(
        self,
        session: Any,
        *,
        clip_id: str,
        fields: dict[str, Any],
        correction_history: list[dict[str, Any]],
    ) -> None:
        sess: Session = session
        clip = sess.get(ClipRow, clip_id)
        if clip is None:
            raise LookupError("clip_not_found")
        row = sess.get(EditorialMetadataRow, clip_id)
        if row is None:
            row = EditorialMetadataRow(clip_id=clip_id, editorial_tags="", editorial_notes="")
            sess.add(row)
        prev_hist: list = list(row.correction_history_json or [])
        prev_hist.extend(correction_history)
        row.correction_history_json = prev_hist[-_MAX_CORRECTIONS:]
        col_map = {
            "editorial_tags": "editorial_tags",
            "editorial_notes": "editorial_notes",
            "visual_cluster_override": "visual_cluster_override",
            "narrative_role": "narrative_role",
            "emotion_profile": "emotion_profile",
            "visual_style": "visual_style",
            "cinematic_style": "cinematic_style",
            "pacing_type": "pacing_type",
            "shot_type": "shot_type",
            "editorial_source_video_id": "editorial_source_video_id",
            "editorial_master_reel_id": "editorial_master_reel_id",
            "quality_score": "quality_score",
            "cinematic_score": "cinematic_score",
            "reviewed": "reviewed",
            "reviewed_by": "reviewed_by",
            "reviewed_at": "reviewed_at",
        }
        for api_key, col in col_map.items():
            if api_key not in fields:
                continue
            val = fields[api_key]
            if api_key == "editorial_tags" and val is not None:
                val = normalize_editorial_tags(str(val))
            setattr(row, col, val)
