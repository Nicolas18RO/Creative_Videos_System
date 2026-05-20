"""Factoría de overrides de categoría editorial."""

from __future__ import annotations

from aicos.application.editorial_category.editorial_category_override_service import EditorialCategoryOverrideService
from aicos.config import AppConfig
from aicos.infrastructure.editorial_category.sql_editorial_category_override_repository import (
    SqlEditorialCategoryOverrideRepository,
)


def build_editorial_category_override_service(cfg: AppConfig | None = None) -> EditorialCategoryOverrideService:
    _ = cfg
    return EditorialCategoryOverrideService(persistence=SqlEditorialCategoryOverrideRepository())
