"""Factoría del pipeline batch OpenCLIP (ensambla infra + servicios)."""

from __future__ import annotations

from aicos.application.multimodal.batch_openclip_pipeline import BatchOpenClipMultimodalPipeline
from aicos.config import AppConfig, get_config
from aicos.core.vector_store import VectorStore
from aicos.infrastructure.multimodal.chroma_visual_sync_adapter import ChromaVisualMetadataSyncAdapter
from aicos.infrastructure.multimodal.ffmpeg_keyframe_export_adapter import FfmpegKeyframeExportAdapter
from aicos.infrastructure.multimodal.openclip_batch_encoder import OpenClipBatchImageEncoder
from aicos.infrastructure.multimodal.sql_clip_visual_job_source import SqlClipVisualJobSource
from aicos.services.multimodal_persistence_adapter import SqlVisualEmbeddingPersistenceAdapter


def build_batch_openclip_pipeline(app_cfg: AppConfig | None = None) -> BatchOpenClipMultimodalPipeline:
    """Construye el pipeline con la configuración actual."""
    cfg = app_cfg or get_config()
    mb = cfg.multimodal_batch
    cm = cfg.cinematic_metadata
    model_tag = f"openclip/{cm.openclip_model}/{cm.openclip_pretrained}"
    jobs = SqlClipVisualJobSource(
        model_tag=model_tag,
        skip_existing_same_model=mb.skip_existing_same_model,
    )
    encoder = OpenClipBatchImageEncoder(model_name=cm.openclip_model, pretrained=cm.openclip_pretrained)
    chroma = None
    if mb.update_chroma:
        chroma = ChromaVisualMetadataSyncAdapter(store=VectorStore())
    return BatchOpenClipMultimodalPipeline(
        batch_cfg=mb,
        cinematic_cfg=cm,
        job_source=jobs,
        keyframes=FfmpegKeyframeExportAdapter(),
        encoder=encoder,
        persister=SqlVisualEmbeddingPersistenceAdapter(),
        chroma_sync=chroma,
    )
