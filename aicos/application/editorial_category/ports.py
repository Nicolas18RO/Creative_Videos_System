"""Puertos de persistencia de overrides de categoría."""

from __future__ import annotations

from typing import Any, Protocol

from aicos.domain.editorial_category.entities import EditorialSceneCategoryOverride


class EditorialCategoryOverridePersistencePort(Protocol):
    def get(self, session: Any, session_id: str, scene_index: int) -> EditorialSceneCategoryOverride | None:
        ...

    def list_by_session(self, session: Any, session_id: str) -> tuple[EditorialSceneCategoryOverride, ...]:
        ...

    def upsert(self, session: Any, override: EditorialSceneCategoryOverride) -> None:
        ...
