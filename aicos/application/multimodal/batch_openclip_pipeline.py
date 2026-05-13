"""Orquestación batch: keyframes → OpenCLIP → SQLite → Chroma."""

from __future__ import annotations

import logging
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from aicos.application.multimodal.ports import (
    ChromaVisualMetadataSyncPort,
    ClipVisualJobSourcePort,
    KeyframeExportPort,
    VisualEmbeddingBatchEncoderPort,
    VisualEmbeddingPersistencePort,
)
from aicos.config import CinematicMetadataConfig, MultimodalBatchConfig
from aicos.domain.multimodal.entities import BatchClipVisualResult, VisualEmbedding
from aicos.domain.multimodal.enums import BatchItemStatus, MultimodalBatchPhase
from aicos.domain.multimodal.rules import visual_fingerprint_from_vector

logger = logging.getLogger(__name__)


class BatchOpenClipMultimodalPipeline:
    """Pipeline batch no bloqueante a nivel de API (un proceso / script por invocación)."""

    def __init__(
        self,
        *,
        batch_cfg: MultimodalBatchConfig,
        cinematic_cfg: CinematicMetadataConfig,
        job_source: ClipVisualJobSourcePort,
        keyframes: KeyframeExportPort,
        encoder: VisualEmbeddingBatchEncoderPort,
        persister: VisualEmbeddingPersistencePort,
        chroma_sync: ChromaVisualMetadataSyncPort | None,
    ) -> None:
        self._batch = batch_cfg
        self._cine = cinematic_cfg
        self._jobs = job_source
        self._kf = keyframes
        self._enc = encoder
        self._persist = persister
        self._chroma = chroma_sync

    def run(self, session: object, *, rescan_all: bool = False) -> list[BatchClipVisualResult]:
        """Procesa lotes hasta agotar candidatos o alcanzar ``max_clips``."""
        if not self._cine.openclip_enabled:
            logger.warning(
                "[MultimodalBatch] cinematic_metadata.openclip_enabled=false "
                "(instala ``pip install .[cinematic]`` y activa en config)"
            )
        results: list[BatchClipVisualResult] = []
        total_seen = 0
        max_n = self._batch.max_clips
        logger.info(
            "[MultimodalBatch] phase=%s batch_size=%s rescan_all=%s",
            MultimodalBatchPhase.DISCOVER.value,
            self._batch.batch_size,
            rescan_all,
        )
        while True:
            if max_n is not None and total_seen >= max_n:
                break
            lim = self._batch.batch_size
            if max_n is not None:
                lim = min(lim, max_n - total_seen)
            targets = self._jobs.iter_targets(session, limit=lim, rescan_all=rescan_all)
            if not targets:
                break
            total_seen += len(targets)
            logger.info(
                "[MultimodalBatch] phase=%s batch=%s",
                MultimodalBatchPhase.KEYFRAMES.value,
                len(targets),
            )
            with tempfile.TemporaryDirectory(prefix="aicos_openclip_") as tmp:
                tmp_path = Path(tmp)
                paths_map: list[tuple[str, str]] = []
                for t in targets:
                    jp = tmp_path / f"{t.clip_id}.jpg"
                    ok = self._kf.export_median_frame(
                        video_path=t.absolute_path,
                        output_jpeg_path=str(jp),
                        width=self._batch.keyframe_width,
                        height=self._batch.keyframe_height,
                    )
                    if not ok:
                        results.append(
                            BatchClipVisualResult(
                                clip_id=t.clip_id,
                                status=BatchItemStatus.FAILED,
                                message="keyframe_export_failed",
                            )
                        )
                        continue
                    paths_map.append((t.clip_id, str(jp)))

                if not paths_map:
                    continue

                logger.info("[MultimodalBatch] phase=%s n=%s", MultimodalBatchPhase.ENCODE.value, len(paths_map))
                paths = [p for _, p in paths_map]
                encoded = self._enc.encode_image_paths_batch(paths)

                chroma_ids: list[str] = []
                for (cid, _), vec in zip(paths_map, encoded, strict=True):
                    if not vec:
                        results.append(
                            BatchClipVisualResult(
                                clip_id=cid,
                                status=BatchItemStatus.FAILED,
                                message="openclip_encode_failed",
                            )
                        )
                        continue
                    model_tag = self._enc.model_tag()
                    fp = visual_fingerprint_from_vector(vec, model_tag=model_tag)
                    now = datetime.now(timezone.utc)
                    emb = VisualEmbedding(
                        clip_id=cid,
                        embedding_vector=tuple(float(x) for x in vec),
                        embedding_model=model_tag,
                        embedding_dimension=len(vec),
                        created_at=now,
                        visual_fingerprint=fp,
                    )
                    logger.info("[MultimodalBatch] phase=%s clip=%s", MultimodalBatchPhase.PERSIST.value, cid)
                    self._persist.persist_visual_embedding(session, emb)
                    results.append(
                        BatchClipVisualResult(
                            clip_id=cid,
                            status=BatchItemStatus.SUCCESS,
                            fingerprint=fp,
                            embedding_dimension=len(vec),
                        )
                    )
                    chroma_ids.append(cid)

                if self._batch.update_chroma and self._chroma is not None and chroma_ids:
                    logger.info(
                        "[MultimodalBatch] phase=%s count=%s",
                        MultimodalBatchPhase.CHROMA.value,
                        len(chroma_ids),
                    )
                    self._chroma.sync_clips(session, chroma_ids)

        logger.info("[MultimodalBatch] phase=%s total=%s", MultimodalBatchPhase.DONE.value, len(results))
        return results
