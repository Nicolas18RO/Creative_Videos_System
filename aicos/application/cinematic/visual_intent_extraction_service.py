"""Caso de uso: intención visual desde texto."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

from aicos.application.cinematic.rule_based_visual_intent import RuleBasedVisualIntentExtractor
from aicos.domain.cinematic.entities import VisualIntent

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class VisualIntentExtractionService:
    _extractor: RuleBasedVisualIntentExtractor = field(default_factory=RuleBasedVisualIntentExtractor)

    def extract(self, transcript: str, scene_text: str) -> tuple[VisualIntent, ...]:
        t0 = time.perf_counter()
        intents = self._extractor.extract(transcript, scene_text)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        logger.info(
            "visual_intent_extraction stage=complete intents=%d elapsed_ms=%.1f",
            len(intents),
            elapsed_ms,
        )
        return intents
