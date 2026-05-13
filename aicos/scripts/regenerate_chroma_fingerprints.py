"""CLI: regenera metadatos multimodales en Chroma desde SQLite (Fase 5.2)."""

from __future__ import annotations

import argparse
import logging
import sys

from aicos.config import get_config
from aicos.database.db import init_db, session_scope
from aicos.services.multimodal_retrieval_factory import build_chroma_fingerprint_regeneration_pipeline

logger = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Regenera fingerprints visuales en Chroma.")
    parser.add_argument(
        "--resume-after",
        type=str,
        default=None,
        help="Cursor ``clip_id``: procesar solo registros con id mayor (orden lexicográfico).",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s %(message)s",
    )
    init_db()
    cfg = get_config()
    if not cfg.multimodal_retrieval.enabled:
        logger.warning("[FingerprintRegen] multimodal_retrieval.enabled=false; salida.")
        return 0
    pipe = build_chroma_fingerprint_regeneration_pipeline(cfg)
    with session_scope() as session:
        stats = pipe.run(session, resume_after_clip_id=args.resume_after)
    logger.info(
        "[FingerprintRegen] done indexed=%s skipped=%s failed=%s elapsed_ms=%s",
        stats.indexed,
        stats.skipped,
        stats.failed,
        stats.elapsed_ms,
    )
    return 0 if stats.failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
