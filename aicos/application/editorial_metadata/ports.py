"""Puertos de lectura/escritura editorial (sin ORM en la firma)."""

from __future__ import annotations

from typing import Any, Protocol

from aicos.domain.editorial_metadata.entities import (
    EditorialFeedbackSignal,
    EditorialMetadataRecord,
)


class EditorialMetadataReadPort(Protocol):
    """Lectura de metadata editorial fusionada con clip/cinemático."""

    def get_by_clip_id(self, session: Any, clip_id: str) -> EditorialMetadataRecord | None:
        """None si el clip no existe en ``clips``."""

    def list_paginated(self, session: Any, *, offset: int, limit: int) -> list[EditorialMetadataRecord]:
        """Lista estable por ``clip_id`` (paginación offset/limit)."""

    def search_by_tags(self, session: Any, *, tag_query: str, limit: int) -> list[EditorialMetadataRecord]:
        """Búsqueda por subcadena en ``editorial_tags`` (OR entre tokens)."""

    def search_by_cluster(self, session: Any, *, cluster_id: str, limit: int, offset: int) -> list[EditorialMetadataRecord]:
        """Clips con override o cluster explícito coincidente."""

    def fetch_editorial_rank_facets(
        self, session: Any, clip_ids: list[str]
    ) -> dict[str, tuple[float | None, float | None, str | None, str | None]]:
        """Por clip: ``quality_score``, ``cinematic_score``, ``visual_cluster_override``, ``editorial_tags``."""


class EditorialMetadataWritePort(Protocol):
    """Persistencia de capa editorial."""

    def save(self, session: Any, record: EditorialMetadataRecord) -> None:
        """Upsert completo (reemplazo de campos editoriales)."""

    def patch(
        self,
        session: Any,
        *,
        clip_id: str,
        fields: dict[str, Any],
        correction_history: list[dict[str, Any]],
    ) -> None:
        """Fusión parcial + historial de correcciones serializado."""


class EditorialFeedbackWritePort(Protocol):
    """Persistencia de feedback humano."""

    def append(self, session: Any, signal: EditorialFeedbackSignal, *, feedback_id: str) -> None:
        """Inserta una fila de feedback."""
