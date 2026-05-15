"""Factoría Fase 6.5 — recomendaciones editoriales (timeline + memoria de estilo)."""

from __future__ import annotations

from aicos.application.editorial_recommendation_engine.editorial_recommendation_service import (
    EditorialRecommendationService,
)
from aicos.config import AppConfig, get_config
from aicos.infrastructure.editorial_dataset.sqlite_creative_timeline_repository import SqlCreativeTimelineRepository
from aicos.infrastructure.editorial_recommendation_engine.delegate_style_retrieval import (
    DelegatingStyleSimilarCreativesPort,
)


def build_editorial_recommendation_service(app_cfg: AppConfig | None = None) -> EditorialRecommendationService:
    cfg = app_cfg or get_config()
    ec = cfg.editorial_recommendation_engine
    timeline = SqlCreativeTimelineRepository()
    style = None
    if ec.use_style_memory and cfg.editorial_style_retrieval.enabled and cfg.editorial_style_embedding.enabled:
        from aicos.services.editorial_style_retrieval_factory import build_editorial_style_retrieval_service

        style = DelegatingStyleSimilarCreativesPort(build_editorial_style_retrieval_service(cfg))
    return EditorialRecommendationService(ec, timeline, style)
