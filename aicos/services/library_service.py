"""CRUD de clips en SQLite."""

from __future__ import annotations

import logging
import uuid
from sqlalchemy import Select, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, load_only

from aicos.database.db import ClipRow, SceneRow
from aicos.models.schemas import ClipSummary, LibraryClipsResponse

logger = logging.getLogger(__name__)


def upsert_clip(
    session: Session,
    *,
    clip_id: str | None,
    filename: str,
    relative_path: str,
    absolute_path: str,
    gender: str | None,
    narrative_function: str | None,
    subcategory: str | None,
    context: str | None,
    variant_number: int | None,
    is_ai_generated: bool,
    semantic_text: str,
    naming_compliant: bool,
    needs_reclassification: bool,
    asset_kind: str,
    file_hash: str | None,
    duration_ms: int | None,
    resolution_width: int | None,
    resolution_height: int | None,
    file_size_bytes: int | None,
    thumbnail_path: str | None,
    embedding_id: str | None,
) -> str:
    """Inserta o actualiza un clip por `absolute_path` único.

    Nota: `file_hash` NO es identidad lógica; puede repetirse entre múltiples clips.
    """
    cid = clip_id or str(uuid.uuid4())
    row = session.get(ClipRow, cid)
    if row is None:
        row = session.execute(
            select(ClipRow).where(ClipRow.absolute_path == absolute_path)
        ).scalar_one_or_none()
    if row is None:
        row = ClipRow(id=cid)
        session.add(row)
    else:
        cid = row.id
    row.filename = filename
    row.relative_path = relative_path
    row.absolute_path = absolute_path
    row.gender = gender
    row.narrative_function = narrative_function
    row.subcategory = subcategory
    row.context = context
    row.variant_number = variant_number
    row.is_ai_generated = is_ai_generated
    row.semantic_text = semantic_text
    row.naming_compliant = naming_compliant
    row.needs_reclassification = needs_reclassification
    row.asset_kind = asset_kind
    row.file_hash = file_hash
    row.duration_ms = duration_ms
    row.resolution_width = resolution_width
    row.resolution_height = resolution_height
    row.file_size_bytes = file_size_bytes
    row.thumbnail_path = thumbnail_path
    row.embedding_id = embedding_id or cid
    nested = session.begin_nested()
    try:
        session.flush()
        nested.commit()
        return row.id
    except IntegrityError as e:
        # Rollback solo del SAVEPOINT; si el conflicto es por absolute_path, recuperamos el id existente.
        nested.rollback()
        existing = session.execute(select(ClipRow).where(ClipRow.absolute_path == absolute_path)).scalar_one_or_none()
        if existing is not None:
            logger.warning(
                "Conflicto UNIQUE(absolute_path); devolviendo registro existente. absolute_path=%s existing_id=%s err=%s",
                absolute_path,
                existing.id,
                str(e.orig) if getattr(e, "orig", None) else str(e),
            )
            try:
                session.expunge(row)
            except Exception:
                pass
            return existing.id
        raise


def max_variant_number(
    session: Session,
    gender: str,
    narrative_function: str,
    subcategory: str,
    context: str | None,
    is_ai_generated: bool,
) -> int:
    """Devuelve el mayor número de variante existente para la clave taxonómica (0 si no hay)."""
    stmt = select(func.max(ClipRow.variant_number)).where(
        ClipRow.gender == gender,
        ClipRow.narrative_function == narrative_function,
        ClipRow.subcategory == subcategory,
        ClipRow.is_ai_generated == is_ai_generated,
    )
    if context:
        stmt = stmt.where(ClipRow.context == context)
    else:
        stmt = stmt.where(or_(ClipRow.context.is_(None), ClipRow.context == ""))
    val = session.execute(stmt).scalar_one_or_none()
    return int(val or 0)


def count_variants(
    session: Session,
    gender: str | None,
    narrative_function: str | None,
    subcategory: str | None,
) -> int:
    """Cuenta clips con la misma terna taxonómica principal."""
    stmt: Select = select(func.count()).select_from(ClipRow).where(
        ClipRow.gender == gender,
        ClipRow.narrative_function == narrative_function,
        ClipRow.subcategory == subcategory,
    )
    return int(session.execute(stmt).scalar_one())


def get_clip_by_id(session: Session, clip_id: str) -> ClipRow | None:
    return session.get(ClipRow, clip_id)


def library_stats(session: Session) -> dict[str, int]:
    total = session.execute(select(func.count()).select_from(ClipRow)).scalar_one()
    compliant = session.execute(
        select(func.count()).select_from(ClipRow).where(ClipRow.naming_compliant.is_(True))
    ).scalar_one()
    return {"total_clips": int(total), "naming_compliant": int(compliant)}


def list_library_clips(session: Session, *, limit: int, offset: int) -> LibraryClipsResponse:
    """Lista clips paginados para exploración (solo columnas necesarias, sin vectores)."""
    lim = max(1, min(int(limit), 200))
    off = max(0, int(offset))
    total = int(session.execute(select(func.count()).select_from(ClipRow)).scalar_one() or 0)
    stmt = (
        select(ClipRow)
        .options(
            load_only(
                ClipRow.id,
                ClipRow.filename,
                ClipRow.relative_path,
                ClipRow.file_hash,
                ClipRow.duration_ms,
                ClipRow.tags,
                ClipRow.semantic_text,
                ClipRow.narrative_function,
                ClipRow.subcategory,
            )
        )
        .order_by(ClipRow.relative_path.asc())
        .limit(lim)
        .offset(off)
    )
    rows = list(session.scalars(stmt).all())
    ids = [r.id for r in rows]
    scene_by_clip: dict[str, str] = {}
    if ids:
        pairs = session.execute(
            select(SceneRow.selected_clip_id, SceneRow.id).where(SceneRow.selected_clip_id.in_(ids))
        ).all()
        for clip_id, scene_id in pairs:
            cid = str(clip_id)
            sid = str(scene_id)
            if cid not in scene_by_clip:
                scene_by_clip[cid] = sid
    items: list[ClipSummary] = []
    for r in rows:
        raw_sem = (r.semantic_text or "").strip()
        excerpt = raw_sem[:280] if raw_sem else None
        items.append(
            ClipSummary(
                clip_id=r.id,
                name=r.filename,
                relative_path=r.relative_path or "",
                file_hash=r.file_hash,
                scene_id=scene_by_clip.get(r.id),
                duration_ms=r.duration_ms,
                tags=r.tags,
                narrative_function=r.narrative_function,
                subcategory=r.subcategory,
                semantic_excerpt=excerpt,
                created_at=None,
            )
        )
    return LibraryClipsResponse(total=total, limit=lim, offset=off, items=items)
