"""Sugerencias de reclasificación M4 (solo lectura + visión; sin escritura en DB)."""

from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from aicos.config import get_config
from aicos.database.db import ClipRow
from aicos.models.schemas import (
    ReclassificationBatchRequest,
    ReclassificationBatchResponse,
    ReclassificationSuggestion,
)
from aicos.services import vision_service
from aicos.services.llm_service import LLMService
from aicos.taxonomy.parser import parse_filename

logger = logging.getLogger(__name__)


async def run_batch(
    session: Session,
    body: ReclassificationBatchRequest,
) -> ReclassificationBatchResponse:
    """Analiza clips marcados y/o listados en ``needs_reclassification.txt``; devuelve sugerencias."""
    cfg = get_config()
    paths = cfg.resolved_paths()
    root = paths["library_root"]
    suggestions: list[ReclassificationSuggestion] = []
    sources: list[str] = []
    seen: set[str] = set()

    llm: LLMService | None = None
    if not cfg.runtime.local_only:
        try:
            llm = LLMService()
        except RuntimeError as e:
            llm = None
            logger.info("LLM no disponible para visión en batch: %s", e)

    async def add_row(row: ClipRow, source: str) -> None:
        if row.id in seen or len(suggestions) >= body.limit:
            return
        seen.add(row.id)
        p = Path(row.absolute_path) if row.absolute_path else Path()
        tax = parse_filename(p.name if p.name else row.filename)
        vision = None
        if cfg.runtime.local_only and p.name:
            vision = vision_service.classify_from_path_heuristic(p)
        elif llm is not None and row.thumbnail_path:
            thumb = Path(row.thumbnail_path)
            if thumb.is_file():
                try:
                    vision = await vision_service.classify_frame(thumb, llm)
                except Exception as ex:
                    logger.warning("Visión omitida para %s: %s", row.id, ex)
        notes = ""
        if vision is None:
            notes = "Sin sugerencia de visión (thumbnail ausente o modo local sin ruta)."
        suggestions.append(
            ReclassificationSuggestion(
                clip_id=row.id,
                relative_path=row.relative_path or "",
                current_narrative_function=row.narrative_function,
                current_subcategory=row.subcategory,
                filename_parse_gender=tax.gender,
                filename_parse_narrative_function=tax.narrative_function,
                filename_parse_subcategory=tax.subcategory,
                vision_suggestion=vision,
                notes=notes,
            )
        )
        sources.append(source)

    if body.use_db_flagged:
        sources.append("clips.needs_reclassification")
        rows = list(
            session.scalars(
                select(ClipRow)
                .where(ClipRow.needs_reclassification.is_(True))
                .order_by(ClipRow.id.asc())
                .limit(body.limit)
            ).all()
        )
        for row in rows:
            await add_row(row, "db")

    if body.include_export_file and len(suggestions) < body.limit:
        report = paths["exports"] / "needs_reclassification.txt"
        if report.is_file():
            sources.append(str(report))
            for line in report.read_text(encoding="utf-8").splitlines():
                if len(suggestions) >= body.limit:
                    break
                rel = line.strip().replace("\\", "/")
                if not rel:
                    continue
                row = session.scalars(select(ClipRow).where(ClipRow.relative_path == rel)).first()
                if row is None:
                    continue
                await add_row(row, "export_file")

    return ReclassificationBatchResponse(suggestions=suggestions, sources=sources)
