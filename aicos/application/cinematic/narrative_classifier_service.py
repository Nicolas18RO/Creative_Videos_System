"""Orquesta proveedores de clasificación narrativa según orden configurable."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass

from aicos.application.cinematic.ports import NarrativeClassifierProvider
from aicos.application.cinematic.rule_based_narrative import RuleBasedNarrativeProvider
from aicos.domain.cinematic.entities import NarrativeClassificationResult

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class NarrativeClassifierService:
    """Caso de uso: narrativa desde texto sin acoplarse a APIs concretas."""

    providers: list[NarrativeClassifierProvider]
    provider_order: tuple[str, ...]

    def classify(
        self,
        transcript: str,
        scene_text: str,
        context: str | None = None,
    ) -> tuple[NarrativeClassificationResult, str]:
        """Retorna (resultado, provider_id usado)."""
        by_id = {p.provider_id: p for p in self.providers}
        t0 = time.perf_counter()
        for pid in self.provider_order:
            prov = by_id.get(pid)
            if prov is None:
                continue
            out = prov.classify(transcript, scene_text, context)
            if out is not None:
                elapsed_ms = (time.perf_counter() - t0) * 1000
                logger.info(
                    "narrative_classification stage=complete provider=%s confidence=%.3f elapsed_ms=%.1f",
                    pid,
                    out.confidence,
                    elapsed_ms,
                )
                return out, pid
        rules = RuleBasedNarrativeProvider()
        out = rules.classify(transcript, scene_text, context)
        assert out is not None
        elapsed_ms = (time.perf_counter() - t0) * 1000
        logger.warning(
            "narrative_classification stage=fallback provider=rules confidence=%.3f elapsed_ms=%.1f",
            out.confidence,
            elapsed_ms,
        )
        return out, rules.provider_id
