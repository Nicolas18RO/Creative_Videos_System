"""Indexado inicial de la biblioteca: escaneo → SQLite → embeddings → ChromaDB."""

from __future__ import annotations

import argparse
import fnmatch
import logging
import sys
from pathlib import Path

from sqlalchemy import select

from aicos.config import get_config
from aicos.core.embedder import Embedder
from aicos.core.vector_store import VectorStore
from aicos.database.db import ClipCinematicMetadataRow, ClipRow, init_db, session_scope
from aicos.services.chroma_clip_metadata import build_chroma_metadata_bundle
from aicos.services.library_service import upsert_clip
from aicos.taxonomy.parser import parse_filename
from aicos.taxonomy.text_builder import build_semantic_text

logger = logging.getLogger(__name__)

VIDEO_EXTENSIONS = {".mp4", ".mov", ".webm", ".avi", ".mkv"}
AUDIO_EXTENSIONS = {".aac", ".wav"}
CHROMA_UPSERT_CHUNK = 500


def _configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def _should_ignore(
    path: Path,
    *,
    library_root: Path,
    ignore_folders: set[str],
    ignore_patterns: list[str],
) -> bool:
    rel = path.relative_to(library_root)
    parts_lower = {p.lower() for p in rel.parts}
    if parts_lower & {f.lower() for f in ignore_folders}:
        return True
    name = path.name
    for pat in ignore_patterns:
        if fnmatch.fnmatch(name, pat) or fnmatch.fnmatch(str(rel), pat):
            return True
    return False


def _iter_media_files(library_root: Path, ignore_folders: set[str], ignore_patterns: list[str]):
    for p in library_root.rglob("*"):
        if not p.is_file():
            continue
        if _should_ignore(p, library_root=library_root, ignore_folders=ignore_folders, ignore_patterns=ignore_patterns):
            continue
        ext = p.suffix.lower()
        if ext in VIDEO_EXTENSIONS or ext in AUDIO_EXTENSIONS:
            yield p


def run_bootstrap(
    library_root: Path | None = None,
    *,
    dry_run: bool = False,
    skip_embeddings: bool = False,
    reset_chroma: bool = False,
    verbose: bool = False,
) -> int:
    _configure_logging(verbose)
    cfg = get_config()
    paths = cfg.resolved_paths()
    root = library_root or paths["library_root"]
    if not root.is_dir():
        logger.error("library_root no es un directorio válido: %s", root)
        return 2

    ignore_folders = set(cfg.library.ignore_folders or [])
    ignore_patterns = list(cfg.library.ignore_patterns or [])

    files = sorted(_iter_media_files(root, ignore_folders, ignore_patterns))
    logger.info("Encontrados %s archivos de media bajo %s", len(files), root)

    noncompliant: list[str] = []
    rows: list[tuple[Path, str, object]] = []

    for fp in files:
        tax = parse_filename(fp)
        rel = str(fp.relative_to(root)).replace("\\", "/")
        sem = build_semantic_text(tax, fp.name)
        rows.append((fp, rel, tax))
        if not tax.is_naming_compliant:
            noncompliant.append(rel)

    exports_dir = paths["exports"]
    exports_dir.mkdir(parents=True, exist_ok=True)
    report_path = exports_dir / "needs_reclassification.txt"
    report_path.write_text("\n".join(noncompliant) + ("\n" if noncompliant else ""), encoding="utf-8")
    logger.info(
        "Taxonomía: %s conformes, %s no conformes. Lista: %s",
        len(files) - len(noncompliant),
        len(noncompliant),
        report_path,
    )

    if dry_run:
        return 0

    init_db()
    ffmpeg = FFmpegService()
    thumbs_dir = paths["thumbnails_cache"]
    thumbs_dir.mkdir(parents=True, exist_ok=True)

    embedder: Embedder | None = None
    store: VectorStore | None = None
    if not skip_embeddings:
        try:
            embedder = Embedder()
            store = VectorStore()
            if reset_chroma:
                store.delete_all()
        except (RuntimeError, ValueError, ImportError) as e:
            logger.error("%s Usa --skip-embeddings para solo SQLite.", e)
            return 3

    chroma_rows: list[tuple[str, str, dict]] = []

    with session_scope() as session:
        for fp, rel, tax in rows:
            sem = build_semantic_text(tax, fp.name)
            file_hash = None
            try:
                file_hash = ffmpeg.compute_file_hash(fp)
            except OSError as e:
                logger.warning("No se pudo hashear %s: %s", fp, e)
            thumb_base = file_hash or fp.stem
            thumb_path = thumbs_dir / f"{thumb_base}_thumb.jpg"
            thumb_ok = False
            if ffmpeg.is_available() and fp.suffix.lower() in VIDEO_EXTENSIONS:
                thumb_ok = ffmpeg.extract_thumbnail(
                    fp,
                    thumb_path,
                    width=cfg.ui.thumbnail_size[0],
                    height=cfg.ui.thumbnail_size[1],
                )
            meta_ff = ffmpeg.get_video_metadata(fp)
            thumb_str = str(thumb_path) if thumb_ok else None

            clip_id = upsert_clip(
                session,
                clip_id=None,
                filename=fp.name,
                relative_path=rel,
                absolute_path=str(fp.resolve()),
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
                duration_ms=meta_ff.duration_ms or None,
                resolution_width=meta_ff.width,
                resolution_height=meta_ff.height,
                file_size_bytes=meta_ff.file_size_bytes,
                thumbnail_path=thumb_str,
                embedding_id=None,
            )

            if embedder and store:
                row_db = session.get(ClipRow, clip_id)
                if row_db is None:
                    row_db = session.execute(select(ClipRow).where(ClipRow.id == clip_id)).scalar_one_or_none()
                cm_row = session.get(ClipCinematicMetadataRow, clip_id) if row_db else None
                if row_db is None:
                    logger.error("No ClipRow tras upsert clip_id=%s", clip_id)
                else:
                    bundle = build_chroma_metadata_bundle(row_db, cm_row)
                    chroma_rows.append((clip_id, sem, bundle))

    if embedder and store and chroma_rows:
        ids = [r[0] for r in chroma_rows]
        docs = [r[1] for r in chroma_rows]
        metas = [r[2] for r in chroma_rows]
        bs = cfg.embeddings.batch_size
        logger.info("Generando embeddings en batch (clips=%s, batch_size=%s)...", len(docs), bs)
        embs = embedder.embed_batch(docs, batch_size=bs)
        for i in range(0, len(ids), CHROMA_UPSERT_CHUNK):
            store.upsert_clips(
                ids[i : i + CHROMA_UPSERT_CHUNK],
                embs[i : i + CHROMA_UPSERT_CHUNK],
                docs[i : i + CHROMA_UPSERT_CHUNK],
                metas[i : i + CHROMA_UPSERT_CHUNK],
            )
        logger.info("Chroma upsert en bloques de %s completado.", CHROMA_UPSERT_CHUNK)

    logger.info("Bootstrap completado.")
    return 0


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Indexa la biblioteca de clips (SQLite + ChromaDB).")
    parser.add_argument("--library-root", type=Path, default=None, help="Raíz de la biblioteca")
    parser.add_argument("--dry-run", action="store_true", help="Solo escaneo y reporte")
    parser.add_argument(
        "--skip-embeddings",
        action="store_true",
        help="Sin embeddings/Chroma (solo SQLite y miniaturas)",
    )
    parser.add_argument("--reset-chroma", action="store_true", help="Borra la colección vectorial antes de indexar")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)
    code = run_bootstrap(
        args.library_root,
        dry_run=args.dry_run,
        skip_embeddings=args.skip_embeddings,
        reset_chroma=args.reset_chroma,
        verbose=args.verbose,
    )
    raise SystemExit(code)


if __name__ == "__main__":
    main(sys.argv[1:])
