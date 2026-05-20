"""Factoría del registry editorial (Fase 6.7.1)."""

from __future__ import annotations

from aicos.application.editorial_registry.editorial_registry_service import EditorialRegistryService
from aicos.config import AppConfig
from aicos.infrastructure.editorial_registry.sql_editorial_registry_repository import SqlEditorialRegistryRepository


def build_editorial_registry_service(cfg: AppConfig | None = None) -> EditorialRegistryService:
    _ = cfg
    return EditorialRegistryService(registry_read=SqlEditorialRegistryRepository())
