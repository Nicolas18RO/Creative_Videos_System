"""Entidad de intención semántica por escena (taxonomía clip + narrativa + emoción)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from aicos.domain.editorial_taxonomy.rules import (
    effective_clip_source_taxonomy,
    effective_emotional_intent,
    effective_narrative_intent,
    intent_label_for_role,
)


@dataclass(frozen=True, slots=True)
class SceneSemanticIntent:
    """Anotación semántica humana-en-el-bucle por escena de entrenamiento."""

    session_id: str
    scene_index: int
    clip_id: str = ""
    auto_clip_source_taxonomy: str = "NATURAL"
    human_clip_source_taxonomy: str | None = None
    auto_narrative_intent: str = "NATURAL"
    human_narrative_intent: str | None = None
    auto_emotional_intent: str = "NEUTRAL"
    human_emotional_intent: str | None = None
    audio_fragment_text: str = ""
    visual_style_label: str = ""
    updated_at: datetime | None = None
    reviewer: str = "system"

    @property
    def effective_clip_source(self) -> str:
        return effective_clip_source_taxonomy(self.auto_clip_source_taxonomy, self.human_clip_source_taxonomy)

    @property
    def effective_narrative_intent(self) -> str:
        return effective_narrative_intent(self.auto_narrative_intent, self.human_narrative_intent)

    @property
    def effective_emotional_intent(self) -> str:
        return effective_emotional_intent(self.auto_emotional_intent, self.human_emotional_intent)

    @property
    def narrative_intent_label(self) -> str:
        return intent_label_for_role(self.effective_narrative_intent)

    @property
    def has_clip_taxonomy_override(self) -> bool:
        return bool((self.human_clip_source_taxonomy or "").strip())

    @property
    def has_narrative_intent_override(self) -> bool:
        return bool((self.human_narrative_intent or "").strip())

    @property
    def has_emotional_intent_override(self) -> bool:
        return bool((self.human_emotional_intent or "").strip())
