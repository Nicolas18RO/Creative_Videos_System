"""Pipeline batch: regeneración Chroma con cursor, tolerancia a fallos y estadísticas."""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

from aicos.application.multimodal_retrieval.chroma_fingerprint_regeneration_service import (
    ChromaFingerprintRegenerationService,
)
from aicos.config import MultimodalRetrievalConfig, get_config
from aicos.domain.multimodal_retrieval.entities import MultimodalIndexStats

logger = logging.getLogger(__name__)


class ChromaFingerprintRegenerationPipeline:
    """Orquesta lotes hasta vaciar cola o superar ``max_failures`` consecutivos por lote vacío."""

    def __init__(
        self,
        *,
        service: ChromaFingerprintRegenerationService,
        retrieval_cfg: MultimodalRetrievalConfig | None = None,
    ) -> None:
        self._svc = service
        self._cfg = retrieval_cfg or get_config().multimodal_retrieval

    def run(
        self,
        session: Any,
        *,
        resume_after_clip_id: str | None = None,
    ) -> MultimodalIndexStats:
        """Procesa toda la cola ordenada por ``clip_id``."""
        t0 = time.perf_counter()
        total_i = total_s = total_f = 0
        cursor: str | None = resume_after_clip_id
        streak_bad = 0
        while True:
            stats, last = self._svc.regenerate_batch(
                session,
                after_clip_id=cursor,
                limit=self._cfg.batch_size,
                continuity_by_clip=None,
            )
            total_i += stats.indexed
            total_s += stats.skipped
            total_f += stats.failed
            if stats.processed == 0:
                break
            if last is None:
                break
            cursor = last
            if stats.indexed == 0 and stats.failed >= stats.processed:
                streak_bad += 1
            else:
                streak_bad = 0
            if streak_bad >= self._cfg.max_failures:
                logger.error(
                    "[FingerprintRegen] abort max_failures=%s cursor=%s",
                    self._cfg.max_failures,
                    cursor,
                )
                break
        elapsed = int((time.perf_counter() - t0) * 1000)
        agg = MultimodalIndexStats(
            indexed=total_i,
            skipped=total_s,
            failed=total_f,
            elapsed_ms=elapsed,
        )
        if self._cfg.persist_stats:
            self._persist_stats_line(cursor, agg)
        logger.info(
            "[BatchProgress] done indexed=%s skipped=%s failed=%s elapsed_ms=%s",
            agg.indexed,
            agg.skipped,
            agg.failed,
            agg.elapsed_ms,
        )
        return agg

    def _persist_stats_line(self, cursor: str | None, stats: MultimodalIndexStats) -> None:
        try:
            paths = get_config().resolved_paths()
            log_dir = paths.get("logs") or Path.home() / ".aicos" / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            path = Path(log_dir) / "chroma_fingerprint_regen.jsonl"
            line = json.dumps(
                {
                    "cursor": cursor,
                    "indexed": stats.indexed,
                    "skipped": stats.skipped,
                    "failed": stats.failed,
                    "elapsed_ms": stats.elapsed_ms,
                },
                ensure_ascii=False,
            )
            path.open("a", encoding="utf-8").write(line + "\n")
        except OSError as e:
            logger.warning("[FingerprintRegen] persist_stats_failed: %s", e)
