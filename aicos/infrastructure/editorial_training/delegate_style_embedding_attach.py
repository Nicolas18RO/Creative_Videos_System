"""Adaptador: delega en ``maybe_attach_style_embedding`` (Fase 6.3 / infra de servicios)."""

from __future__ import annotations

from typing import Any

from aicos.application.editorial_training.ports import EditorialStyleEmbeddingAttachPort
from aicos.config import AppConfig
from aicos.domain.editorial_dataset.entities import CreativeTimeline


class ServiceEditorialStyleEmbeddingAttachAdapter(EditorialStyleEmbeddingAttachPort):
    def __init__(self, app_cfg: AppConfig) -> None:
        self._app_cfg = app_cfg

    def attach_if_configured(self, session: Any, timeline: CreativeTimeline) -> CreativeTimeline:
        from aicos.services.editorial_style_embedding_factory import maybe_attach_style_embedding

        return maybe_attach_style_embedding(session, timeline, self._app_cfg)
