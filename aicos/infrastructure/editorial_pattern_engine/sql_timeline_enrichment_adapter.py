"""Enriquecimiento de timeline: SQLite cinematográfico + taxonomía de clips."""

from __future__ import annotations

import logging
from typing import Any, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from aicos.application.editorial_pattern_engine.ports import TimelinePatternEnrichmentPort
from aicos.database.db import ClipCinematicMetadataRow, ClipRow
from aicos.domain.cinematic_metadata.entities import SourceVideoMetadata
from aicos.domain.editorial_pattern_engine.entities import (
    CinematicClipSlice,
    LibraryClipSlice,
    TimelineEnrichmentBundle,
)
from aicos.services.cinematic_metadata_mapping import clip_cinematic_row_to_domain

logger = logging.getLogger(__name__)


def _to_slice(meta: SourceVideoMetadata | None) -> CinematicClipSlice | None:
    if meta is None:
        return None
    return CinematicClipSlice(
        source_video_id=meta.source_video_id or "",
        master_reel_id=meta.master_reel_id or "",
        production_group=meta.production_group or "",
        camera_id=meta.camera_id or "",
        shooting_session_id=meta.shooting_session_id or "",
        visual_cluster_id_explicit=meta.visual_cluster_id_explicit or "",
    )


class SqlTimelinePatternEnrichmentAdapter(TimelinePatternEnrichmentPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def load_bundle(self, session: Any, clip_ids: Sequence[str]) -> TimelineEnrichmentBundle:
        sess = session if session is not None else self._session
        ids = tuple(dict.fromkeys(str(x) for x in clip_ids if x))  # dedupe preserve order
        if not ids:
            return TimelineEnrichmentBundle(cinematic_by_clip={}, library_by_clip={})

        cine_map: dict[str, CinematicClipSlice] = {}
        stmt_c = select(ClipCinematicMetadataRow).where(ClipCinematicMetadataRow.clip_id.in_(ids))
        for row in sess.scalars(stmt_c).all():
            dom = clip_cinematic_row_to_domain(row)
            sl = _to_slice(dom)
            if sl is not None:
                cine_map[row.clip_id] = sl

        lib_map: dict[str, LibraryClipSlice] = {}
        stmt_l = select(ClipRow).where(ClipRow.id.in_(ids))
        for row in sess.scalars(stmt_l).all():
            lib_map[row.id] = LibraryClipSlice(
                narrative_function=(row.narrative_function or "") or "",
                subcategory=(row.subcategory or "") or "",
                context=(row.context or "") or "",
            )
        logger.debug("[PatternEngineEnrich] clips=%s cine=%s lib=%s", len(ids), len(cine_map), len(lib_map))
        return TimelineEnrichmentBundle(cinematic_by_clip=cine_map, library_by_clip=lib_map)
