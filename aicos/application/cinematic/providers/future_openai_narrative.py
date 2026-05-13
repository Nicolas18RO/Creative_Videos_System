"""Stub para futura integración OpenAI (no llamar red en local-first)."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from aicos.domain.cinematic.entities import NarrativeClassificationResult

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class FutureOpenAINarrativeProvider:
    @property
    def provider_id(self) -> str:
        return "future_openai"

    def classify(
        self,
        transcript: str,
        scene_text: str,
        context: str | None = None,
    ) -> NarrativeClassificationResult | None:
        logger.debug("narrative_classification stage=provider_skip model=future_openai")
        return None
