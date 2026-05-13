"""Reconstruye vectores en ChromaDB desde SQLite (mismo proveedor que `config.yaml`)."""

from __future__ import annotations

import argparse
import logging
import sys

from sqlalchemy import select

from aicos.config import get_config
from aicos.core.embedder import Embedder
from aicos.core.vector_store import VectorStore
from aicos.database.db import ClipCinematicMetadataRow, ClipRow, init_db, session_scope
from aicos.services.chroma_clip_metadata import build_chroma_metadata_bundle

logger = logging.getLogger(__name__)

CHROMA_UPSERT_CHUNK = 500


def _configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def run_reindex(*, reset: bool = True, verbose: bool = False) -> int:
    _configure_logging(verbose)
    cfg = get_config()
    init_db()
    try:
        embedder = Embedder()
        store = VectorStore()
    except (RuntimeError, ValueError, ImportError) as e:
        logger.error("No se pudo inicializar embeddings/Chroma: %s", e)
        return 3

    if reset:
        logger.info("Vacando colección Chroma %s...", store.collection_name)
        store.delete_all()

    with session_scope() as session:
        rows = list(session.scalars(select(ClipRow).order_by(ClipRow.relative_path)).all())
        cm_rows = list(session.scalars(select(ClipCinematicMetadataRow)).all())
        cm_by_id = {c.clip_id: c for c in cm_rows}

    triples: list[tuple[str, str, dict]] = []
    for r in rows:
        sem = (r.semantic_text or "").strip()
        if not sem:
            continue
        triples.append((r.id, sem, build_chroma_metadata_bundle(r, cm_by_id.get(r.id))))

    if not triples:
        logger.warning("No hay clips con semantic_text en SQLite; nada que indexar.")
        return 0

    ids = [t[0] for t in triples]
    docs = [t[1] for t in triples]
    metas = [t[2] for t in triples]
    bs = cfg.embeddings.batch_size
    logger.info(
        "Reindex: clips=%s colección=%s batch_size=%s reset=%s",
        len(docs),
        store.collection_name,
        bs,
        reset,
    )
    embs = embedder.embed_batch(docs, batch_size=bs)
    for i in range(0, len(ids), CHROMA_UPSERT_CHUNK):
        store.upsert_clips(
            ids[i : i + CHROMA_UPSERT_CHUNK],
            embs[i : i + CHROMA_UPSERT_CHUNK],
            docs[i : i + CHROMA_UPSERT_CHUNK],
            metas[i : i + CHROMA_UPSERT_CHUNK],
        )
    logger.info("Reindex vectorial completado.")
    return 0


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Regenera ChromaDB desde SQLite usando el proveedor de embeddings configurado."
    )
    parser.add_argument(
        "--no-reset",
        action="store_true",
        help="No borrar la colección antes (solo upsert; misma dimensión/modelo)",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)
    code = run_reindex(reset=not args.no_reset, verbose=args.verbose)
    raise SystemExit(code)


if __name__ == "__main__":
    main(sys.argv[1:])
