"""Sincronización SQLite tras un move/rename verificado. Sin tablas nuevas."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from aicos.database.db import ClipRow
from aicos.services import library_service
from aicos.taxonomy.parser import parse_filename
from aicos.taxonomy.text_builder import build_semantic_text

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class OrganizationSyncResult:
    synced: bool
    clip_id: str | None
    message: str


def paths_are_consistent(*, absolute_path: str, relative_path: str, library_root: Path, dest: Path) -> bool:
    """True si los paths de DB coinciden con el archivo físico bajo library_root."""
    try:
        dest_res = dest.resolve()
        root_res = library_root.resolve()
        expected_rel = str(dest_res.relative_to(root_res)).replace("\\", "/")
        return (
            dest_res.is_file()
            and Path(absolute_path).resolve() == dest_res
            and relative_path.replace("\\", "/") == expected_rel
        )
    except (OSError, ValueError):
        return False


def sync_organized_clip(
    session: Session,
    *,
    destination_path: Path,
    library_root: Path,
    source_path: Path | None = None,
    clip_id: str | None = None,
    file_hash: str | None = None,
    duration_ms: int | None = None,
    resolution_width: int | None = None,
    resolution_height: int | None = None,
    file_size_bytes: int | None = None,
    thumbnail_path: str | None = None,
    semantic_text: str | None = None,
) -> OrganizationSyncResult:
    """Actualiza o inserta el clip solo si el destino existe en disco.

    Busca primero por `clip_id`, luego por el path de origen (fila pre-move) y
    por el path de destino (operación repetida). No escribe si el archivo no está.
    """
    dest = Path(destination_path)
    root = Path(library_root)
    try:
        dest_res = dest.resolve()
    except OSError as exc:
        return OrganizationSyncResult(False, clip_id, f"No se puede resolver el destino: {exc}")

    if not dest_res.is_file():
        return OrganizationSyncResult(
            False,
            clip_id,
            "No se actualiza SQLite: el destino no existe en disco.",
        )

    try:
        rel = str(dest_res.relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return OrganizationSyncResult(
            False,
            clip_id,
            "No se actualiza SQLite: el destino no está bajo library_root.",
        )

    tax = parse_filename(dest_res.name)
    sem = semantic_text if semantic_text is not None else build_semantic_text(tax, dest_res.name)
    source_abs = str(Path(source_path).resolve()) if source_path is not None else None

    existing = library_service.find_clip_for_organization(
        session,
        clip_id=clip_id,
        source_absolute_path=source_abs,
        destination_absolute_path=str(dest_res),
    )
    existing_id = existing.id if existing is not None else clip_id

    try:
        new_id = library_service.upsert_clip(
            session,
            clip_id=existing_id,
            filename=dest_res.name,
            relative_path=rel,
            absolute_path=str(dest_res),
            gender=tax.gender,
            narrative_function=tax.narrative_function,
            subcategory=tax.subcategory,
            context=tax.context,
            variant_number=tax.variant_number,
            is_ai_generated=tax.is_ai_generated,
            semantic_text=sem,
            naming_compliant=tax.is_naming_compliant,
            needs_reclassification=not tax.is_naming_compliant,
            asset_kind=tax.asset_kind,
            file_hash=file_hash,
            duration_ms=duration_ms,
            resolution_width=resolution_width,
            resolution_height=resolution_height,
            file_size_bytes=file_size_bytes,
            thumbnail_path=thumbnail_path,
            embedding_id=None,
        )
        session.flush()
    except IntegrityError as exc:
        logger.warning("Sync de organización en conflicto: %s", exc)
        return OrganizationSyncResult(False, existing_id, f"Conflicto al sincronizar SQLite: {exc}")

    row = session.get(ClipRow, new_id)
    if row is None or not paths_are_consistent(
        absolute_path=row.absolute_path,
        relative_path=row.relative_path,
        library_root=root,
        dest=dest_res,
    ):
        return OrganizationSyncResult(False, new_id, "Verificación SQLite/filesystem falló.")

    return OrganizationSyncResult(True, new_id, "SQLite sincronizado con el destino físico.")
