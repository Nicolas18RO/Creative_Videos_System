"""Factoría de intención semántica editorial."""

from __future__ import annotations

from aicos.application.editorial_semantic_intent.editorial_semantic_intent_service import EditorialSemanticIntentService
from aicos.config import AppConfig
from aicos.infrastructure.editorial_semantic_intent.library_clip_taxonomy_resolver import LibraryClipTaxonomyResolver
from aicos.infrastructure.editorial_semantic_intent.sql_editorial_semantic_intent_repository import (
    SqlEditorialSemanticIntentRepository,
)


def build_editorial_semantic_intent_service(cfg: AppConfig | None = None) -> EditorialSemanticIntentService:
    _ = cfg
    return EditorialSemanticIntentService(
        persistence=SqlEditorialSemanticIntentRepository(),
        clip_taxonomy=LibraryClipTaxonomyResolver(),
    )
