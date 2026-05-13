"""CLI: batch OpenCLIP sobre toda la biblioteca (Fase 5.1)."""

from __future__ import annotations

import argparse
import logging
import sys

from aicos.config import get_config
from aicos.database.db import init_db, session_scope
from aicos.domain.multimodal.enums import BatchItemStatus
from aicos.services.multimodal_batch_factory import build_batch_openclip_pipeline

logger = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Genera embeddings visuales OpenCLIP por lotes y sincroniza Chroma."
    )
    parser.add_argument(
        "--rescan-all",
        action="store_true",
        help="Reprocesa clips aunque ya exista embedding del mismo modelo.",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    cfg = get_config()
    if not cfg.multimodal_batch.enabled:
        logger.error("multimodal_batch.enabled=false en config.yaml")
        return 2
    init_db()
    pipe = build_batch_openclip_pipeline(cfg)
    ok = fail = 0
    with session_scope() as session:
        results = pipe.run(session, rescan_all=args.rescan_all)
        for r in results:
            if r.status == BatchItemStatus.SUCCESS:
                ok += 1
            elif r.status == BatchItemStatus.FAILED:
                fail += 1
        session.commit()
    logger.info("[batch_openclip] success=%s failed=%s", ok, fail)
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
