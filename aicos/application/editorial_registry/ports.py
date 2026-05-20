"""Puertos del registry editorial."""

from __future__ import annotations

from typing import Any, Protocol

from aicos.domain.editorial_registry.entities import EditorialRegistrySession


class EditorialRegistryReadPort(Protocol):
    def list_sessions(
        self,
        session: Any,
        *,
        status: str | None = None,
    ) -> tuple[EditorialRegistrySession, ...]:
        ...
