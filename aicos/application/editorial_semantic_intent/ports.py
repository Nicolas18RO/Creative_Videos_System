"""Puertos de intención semántica editorial."""

from __future__ import annotations

from typing import Any, Protocol

from aicos.domain.editorial_taxonomy.entities import SceneSemanticIntent


class ClipSourceTaxonomyResolverPort(Protocol):
    def resolve_clip_source_taxonomy(self, session: Any, clip_id: str) -> str:
        """Taxonomía inferida desde carpeta/nombre del clip en biblioteca."""
        ...


class EditorialSemanticIntentPersistencePort(Protocol):
    def get(self, session: Any, session_id: str, scene_index: int) -> SceneSemanticIntent | None:
        ...

    def list_by_session(self, session: Any, session_id: str) -> tuple[SceneSemanticIntent, ...]:
        ...

    def upsert(self, session: Any, intent: SceneSemanticIntent) -> None:
        ...
