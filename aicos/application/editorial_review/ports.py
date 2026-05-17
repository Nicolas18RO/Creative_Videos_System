"""Puertos de persistencia — revisión editorial."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from aicos.domain.editorial_review.entities import EditorialSceneMergeRecord, EditorialSceneReviewState


@runtime_checkable
class EditorialSceneReviewPersistencePort(Protocol):
    def list_by_session(self, session: Any, session_id: str) -> tuple[EditorialSceneReviewState, ...]:
        ...

    def get(self, session: Any, session_id: str, scene_id: str) -> EditorialSceneReviewState | None:
        ...

    def upsert(self, session: Any, session_id: str, state: EditorialSceneReviewState) -> None:
        ...

    def upsert_many(self, session: Any, session_id: str, states: tuple[EditorialSceneReviewState, ...]) -> None:
        ...

    def delete_by_session(self, session: Any, session_id: str) -> None:
        ...


@runtime_checkable
class EditorialSceneMergePersistencePort(Protocol):
    def list_by_session(self, session: Any, session_id: str) -> tuple[EditorialSceneMergeRecord, ...]:
        ...

    def save(self, session: Any, record: EditorialSceneMergeRecord) -> None:
        ...
