"""Infraestructura multimodal: OpenCLIP batch, keyframes, sync Chroma."""

from aicos.infrastructure.multimodal.chroma_visual_sync_adapter import ChromaVisualMetadataSyncAdapter
from aicos.infrastructure.multimodal.ffmpeg_keyframe_export_adapter import FfmpegKeyframeExportAdapter
from aicos.infrastructure.multimodal.openclip_batch_encoder import OpenClipBatchImageEncoder
from aicos.infrastructure.multimodal.sql_clip_visual_job_source import SqlClipVisualJobSource

__all__ = [
    "ChromaVisualMetadataSyncAdapter",
    "FfmpegKeyframeExportAdapter",
    "OpenClipBatchImageEncoder",
    "SqlClipVisualJobSource",
]
