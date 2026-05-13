"""Factoría: pipeline de regeneración de fingerprints Chroma (Fase 5.2)."""

from __future__ import annotations

from aicos.application.multimodal_retrieval.chroma_fingerprint_regeneration_service import (
    ChromaFingerprintRegenerationService,
)
from aicos.application.multimodal_retrieval.chroma_regeneration_pipeline import (
    ChromaFingerprintRegenerationPipeline,
)
from aicos.config import AppConfig, get_config
from aicos.infrastructure.multimodal_retrieval.chroma_multimodal_writer import ChromaMultimodalWriter
from aicos.infrastructure.multimodal_retrieval.sqlite_visual_fingerprint_reader import (
    SqliteVisualFingerprintReader,
)


def build_chroma_fingerprint_regeneration_pipeline(app_cfg: AppConfig | None = None) -> ChromaFingerprintRegenerationPipeline:
    """Ensambla lectura SQLite, servicio de aplicación y escritor vía ``VectorStore``."""
    cfg = app_cfg or get_config()
    reader = SqliteVisualFingerprintReader()
    writer = ChromaMultimodalWriter(retrieval_cfg=cfg.multimodal_retrieval)
    svc = ChromaFingerprintRegenerationService(
        batch_reader=reader,
        writer=writer,
        retrieval_cfg=cfg.multimodal_retrieval,
        cinematic_cfg=cfg.cinematic_metadata,
    )
    return ChromaFingerprintRegenerationPipeline(service=svc, retrieval_cfg=cfg.multimodal_retrieval)
