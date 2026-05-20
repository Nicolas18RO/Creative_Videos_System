"""Entidades de override de categoría editorial por escena."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class EditorialSceneCategoryOverride:
    """Override humano de categoría; auto_narrative_role es inmutable tras la primera detección."""

    session_id: str
    scene_index: int
    auto_narrative_role: str
    human_narrative_role: str | None
    updated_at: datetime | None = None
    reviewer: str = "human"

    @property
    def has_human_override(self) -> bool:
        return bool((self.human_narrative_role or "").strip())

    @property
    def effective_role(self) -> str:
        from aicos.domain.editorial_category.rules import effective_narrative_role

        return effective_narrative_role(self.auto_narrative_role, self.human_narrative_role)
