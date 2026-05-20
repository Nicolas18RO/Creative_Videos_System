"""Categorías editoriales y overrides humanos (Fase 6.7.X)."""

from aicos.domain.editorial_category.entities import EditorialSceneCategoryOverride
from aicos.domain.editorial_category.rules import (
    EDITORIAL_NARRATIVE_ROLES,
    effective_narrative_role,
    normalize_narrative_role,
    should_persist_human_override,
)

__all__ = [
    "EDITORIAL_NARRATIVE_ROLES",
    "EditorialSceneCategoryOverride",
    "effective_narrative_role",
    "normalize_narrative_role",
    "should_persist_human_override",
]
