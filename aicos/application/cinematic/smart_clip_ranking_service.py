"""Ranking multi-factor y contextual (Fase 1 + Fase 2)."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass

from aicos.config import CinematicIntelConfig
from aicos.domain.cinematic.entities import SmartRankingBreakdown, SmartRankingInput

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class SmartClipRankingService:
    """Combina señales semánticas, emocionales, narrativas y feedback (legacy interno)."""

    config: CinematicIntelConfig

    def score(self, inp: SmartRankingInput) -> SmartRankingBreakdown:
        t0 = time.perf_counter()
        w = {
            "semantic_similarity": self.config.weight_semantic_similarity,
            "emotional_compatibility": self.config.weight_emotional_compatibility,
            "narrative_compatibility": self.config.weight_narrative_compatibility,
            "pacing_compatibility": self.config.weight_pacing_compatibility,
            "cinematic_compatibility": self.config.weight_cinematic_compatibility,
            "visual_intent_compatibility": self.config.weight_visual_intent_compatibility,
            "feedback_score": self.config.weight_feedback_score,
            "historical_performance": self.config.weight_historical_performance,
        }
        factors = {
            "semantic_similarity": max(0.0, min(1.0, inp.semantic_similarity)),
            "emotional_compatibility": max(0.0, min(1.0, inp.emotional_compatibility)),
            "narrative_compatibility": max(0.0, min(1.0, inp.narrative_compatibility)),
            "pacing_compatibility": max(0.0, min(1.0, inp.pacing_compatibility)),
            "cinematic_compatibility": max(0.0, min(1.0, inp.cinematic_compatibility)),
            "visual_intent_compatibility": max(0.0, min(1.0, inp.visual_intent_compatibility)),
            "feedback_score": max(0.0, min(1.0, inp.feedback_score)),
            "historical_performance": max(0.0, min(1.0, inp.historical_performance)),
        }
        total_w = sum(w.values()) or 1.0
        weighted = {k: factors[k] * (w[k] / total_w) for k in w}
        final = sum(weighted.values())
        elapsed_ms = (time.perf_counter() - t0) * 1000
        logger.info(
            "semantic_matching stage=smart_rank final=%.4f elapsed_ms=%.1f factors=%s",
            final,
            elapsed_ms,
            {k: round(v, 4) for k, v in factors.items()},
        )
        return SmartRankingBreakdown(final_score=final, weighted=weighted, weights_used=w)
