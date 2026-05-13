"""Caso de uso: análisis emocional local."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

from aicos.application.cinematic.rule_based_emotion import RuleBasedEmotionAnalyzer
from aicos.domain.cinematic.entities import EmotionAnalysis

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class EmotionAnalysisService:
    """Servicio de emoción; extensible con proveedor por embeddings locales."""

    deterministic: bool = True
    _analyzer: RuleBasedEmotionAnalyzer = field(default_factory=RuleBasedEmotionAnalyzer)

    def analyze(
        self,
        transcript: str,
        scene_text: str,
        *,
        pacing_hint: str | None = None,
        keywords: tuple[str, ...] = (),
    ) -> EmotionAnalysis:
        t0 = time.perf_counter()
        extra = " ".join(keywords) if keywords else ""
        result = self._analyzer.analyze(f"{transcript} {extra}", scene_text, pacing_hint=pacing_hint)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        logger.info(
            "emotion_analysis stage=complete mode=%s primary=%s intensity=%.3f elapsed_ms=%.1f",
            "deterministic" if self.deterministic else "embedding_stub",
            result.primary_emotion.value,
            result.emotional_intensity,
            elapsed_ms,
        )
        return result
