"""Orquesta timeline + memoria de estilo y delega la lógica pura al dominio."""

from __future__ import annotations

import logging
from typing import Any

from aicos.application.editorial_dataset.ports import CreativeTimelinePersistenceReadPort
from aicos.application.editorial_recommendation_engine.ports import StyleSimilarCreativesPort
from aicos.config import EditorialRecommendationEngineConfig
from aicos.domain.editorial_recommendation.plan_builder import build_editorial_recommendation_plan
from aicos.domain.editorial_recommendation.entities import EditorialRecommendationPlan, StyleMemoryPeerRef

logger = logging.getLogger(__name__)


class EditorialRecommendationService:
    def __init__(
        self,
        cfg: EditorialRecommendationEngineConfig,
        timeline_read: CreativeTimelinePersistenceReadPort,
        style_similar: StyleSimilarCreativesPort | None,
    ) -> None:
        self._cfg = cfg
        self._timeline_read = timeline_read
        self._style_similar = style_similar

    def build_plan(self, session: Any, *, creative_id: str) -> EditorialRecommendationPlan | None:
        if not self._cfg.enabled:
            return None
        anchor = self._timeline_read.get_by_creative_id(session, creative_id)
        if anchor is None:
            return None
        peers: tuple[StyleMemoryPeerRef, ...] = ()
        if self._cfg.use_style_memory and self._style_similar is not None:
            try:
                hits = self._style_similar.retrieve_hits(
                    session,
                    creative_id,
                    max(1, min(20, self._cfg.style_memory_top_k)),
                )
                peers = tuple(
                    StyleMemoryPeerRef(h.creative_id, float(h.hybrid_score))
                    for h in hits
                    if h.hybrid_score >= self._cfg.style_memory_min_peer_score
                )
            except Exception:
                logger.exception("[EditorialRecommendation] style_memory_failed creative=%s", creative_id)
                peers = ()
        return build_editorial_recommendation_plan(
            anchor,
            peers,
            pacing_high_threshold=self._cfg.pacing_high_threshold,
            pacing_low_threshold=self._cfg.pacing_low_threshold,
        )
