"""Servicio de aplicación: validar huellas, construir payloads y upsert en Chroma."""

from __future__ import annotations

import logging
import time
from typing import Any

from aicos.application.multimodal_retrieval.ports import (
    ChromaMultimodalWritePort,
    MultimodalRegenWorkUnitBatchPort,
)
from aicos.config import CinematicMetadataConfig, MultimodalRetrievalConfig
from aicos.domain.multimodal_retrieval.entities import (
    ChromaFingerprintPayload,
    MultimodalContinuityHints,
    MultimodalIndexStats,
    MultimodalRegenWorkUnit,
)
from aicos.services.chroma_multimodal_metadata import build_multimodal_chroma_metadata

logger = logging.getLogger(__name__)

_MIN_FP_LEN = 8


class ChromaFingerprintRegenerationService:
    """Regenera metadatos multimodales en Chroma a partir de SQLite (sin romper embeddings textuales)."""

    def __init__(
        self,
        *,
        batch_reader: MultimodalRegenWorkUnitBatchPort,
        writer: ChromaMultimodalWritePort,
        retrieval_cfg: MultimodalRetrievalConfig,
        cinematic_cfg: CinematicMetadataConfig,
    ) -> None:
        self._reader = batch_reader
        self._writer = writer
        self._cfg = retrieval_cfg
        self._cine = cinematic_cfg

    def _validate_unit(self, unit: MultimodalRegenWorkUnit) -> tuple[bool, str]:
        v = unit.visual
        fp = (v.fingerprint or "").strip()
        if not fp or len(fp) < _MIN_FP_LEN:
            return False, "empty_or_short_fingerprint"
        if v.embedding_dimension <= 0:
            return False, "bad_dimension"
        vec = unit.embedding_vector
        if vec is None:
            return False, "missing_embedding_json"
        if len(vec) != v.embedding_dimension:
            return False, "dimension_mismatch"
        mt = (v.embedding_model or "").strip()
        if not mt.startswith("openclip/"):
            return False, "incompatible_model"
        expected = f"openclip/{self._cine.openclip_model}/{self._cine.openclip_pretrained}"
        if self._cfg.strict_model_match and mt != expected:
            return False, "model_tag_mismatch"
        return True, ""

    def regenerate_batch(
        self,
        session: Any,
        *,
        after_clip_id: str | None,
        limit: int,
        continuity_by_clip: dict[str, MultimodalContinuityHints] | None = None,
    ) -> tuple[MultimodalIndexStats, str | None]:
        """Procesa un lote; devuelve estadísticas y último ``clip_id`` procesado (cursor).

        Args:
            continuity_by_clip: mapa opcional ``clip_id -> MultimodalContinuityHints``.
        """
        t0 = time.perf_counter()
        indexed = skipped = validation_failed = write_failed = 0
        last_id: str | None = None
        units = self._reader.fetch_work_units(session, limit=limit, after_clip_id=after_clip_id)
        payloads: list[ChromaFingerprintPayload] = []
        for u in units:
            last_id = u.visual.clip_id
            if self._cfg.skip_missing_fingerprints and not (u.visual.fingerprint or "").strip():
                skipped += 1
                logger.info(
                    "[FingerprintRegen] clip=%s regenerated=False reason=skip_missing_fingerprint",
                    u.visual.clip_id,
                )
                continue
            ok, reason = self._validate_unit(u)
            if not ok:
                validation_failed += 1
                logger.warning(
                    "[FingerprintRegen] clip=%s regenerated=False reason=%s",
                    u.visual.clip_id,
                    reason,
                )
                continue
            cont = None
            if continuity_by_clip is not None:
                cont = continuity_by_clip.get(u.visual.clip_id)
            meta = build_multimodal_chroma_metadata(
                facet=u.facet,
                visual=u.visual,
                continuity=cont,
                regenerate=self._cfg.regenerate_metadata,
            )
            payloads.append(
                ChromaFingerprintPayload(
                    chroma_id=u.visual.clip_id,
                    metadata=meta,
                    embedding=u.embedding_vector,
                )
            )
            logger.info(
                "[FingerprintRegen] clip=%s regenerated=True fp_len=%s",
                u.visual.clip_id,
                len(u.visual.fingerprint or ""),
            )
        if payloads:
            try:
                self._writer.upsert_multimodal(
                    session,
                    payloads,
                    update_existing=self._cfg.update_existing,
                )
                indexed = len(payloads)
            except Exception as e:
                logger.exception("[ChromaUpsert] batch_failed error=%s", e)
                write_failed = len(payloads)
                indexed = 0
        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        stats = MultimodalIndexStats(
            indexed=indexed,
            skipped=skipped,
            failed=validation_failed + write_failed,
            elapsed_ms=elapsed_ms,
            processed=len(units),
        )
        logger.info(
            "[BatchProgress] processed=%s indexed=%s skipped=%s failed=%s elapsed_ms=%s",
            stats.processed,
            stats.indexed,
            stats.skipped,
            stats.failed,
            stats.elapsed_ms,
        )
        return stats, last_id
