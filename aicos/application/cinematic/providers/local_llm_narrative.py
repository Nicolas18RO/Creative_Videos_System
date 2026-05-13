"""Proveedor narrativo local (Ollama/llama.cpp reservado)."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from aicos.domain.cinematic.entities import NarrativeClassificationResult

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class LocalLLMNarrativeProvider:
    """Cadena opcional; por defecto no activo — el servicio cae a reglas."""

    enabled: bool = False

    @property
    def provider_id(self) -> str:
        return "local_llm"

    def classify(
        self,
        transcript: str,
        scene_text: str,
        context: str | None = None,
    ) -> NarrativeClassificationResult | None:
        if not self.enabled:
            logger.debug(
                "narrative_classification stage=provider_skip model=local_llm reason=disabled"
            )
            return None
        logger.info("narrative_classification stage=provider_stub model=local_llm")
        return None
