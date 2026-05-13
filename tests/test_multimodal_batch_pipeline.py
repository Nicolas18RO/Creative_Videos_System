"""Tests del pipeline batch multimodal (mocks, sin GPU)."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

from aicos.application.multimodal.batch_openclip_pipeline import BatchOpenClipMultimodalPipeline
from aicos.config import CinematicMetadataConfig, MultimodalBatchConfig
from aicos.domain.multimodal.entities import ClipVisualJobTarget
from aicos.domain.multimodal.enums import BatchItemStatus


def test_batch_pipeline_happy_path() -> None:
    mb = MultimodalBatchConfig(batch_size=4, max_clips=2, update_chroma=False)
    cm = CinematicMetadataConfig(openclip_enabled=True)
    jobs = MagicMock()
    jobs.iter_targets.return_value = [
        ClipVisualJobTarget(clip_id="a1", absolute_path="/v/a.mp4"),
        ClipVisualJobTarget(clip_id="b1", absolute_path="/v/b.mp4"),
    ]
    kf = MagicMock()
    kf.export_median_frame.return_value = True
    enc = MagicMock()
    enc.model_tag.return_value = "openclip/test/x"
    enc.encode_image_paths_batch.return_value = [[0.1, 0.2], [0.3, 0.4]]
    persist = MagicMock()
    pipe = BatchOpenClipMultimodalPipeline(
        batch_cfg=mb,
        cinematic_cfg=cm,
        job_source=jobs,
        keyframes=kf,
        encoder=enc,
        persister=persist,
        chroma_sync=None,
    )
    sess = MagicMock()
    out = pipe.run(sess, rescan_all=False)
    assert len(out) == 2
    assert all(r.status == BatchItemStatus.SUCCESS for r in out)
    assert persist.persist_visual_embedding.call_count == 2


def test_visual_embedding_entity_dimension_guard() -> None:
    from aicos.domain.multimodal.entities import VisualEmbedding

    try:
        VisualEmbedding(
            clip_id="x",
            embedding_vector=(0.1, 0.2),
            embedding_model="m",
            embedding_dimension=3,
            created_at=datetime.now(timezone.utc),
        )
        assert False, "expected ValueError"
    except ValueError:
        pass
