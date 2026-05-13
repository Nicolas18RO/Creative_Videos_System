"""Puertos Fase 5.2: lectura de huellas y escritura multimodal en Chroma (sin ORM/Chroma en aplicación)."""

from __future__ import annotations

from typing import Any, Protocol

from aicos.domain.multimodal_retrieval.entities import (
    ChromaFingerprintPayload,
    MultimodalRegenWorkUnit,
    VisualFingerprintRecord,
)


class VisualFingerprintReadPort(Protocol):
    """Lectura de huellas persistidas (SQLite vía adaptador)."""

    def fetch_batch(
        self,
        session: Any,
        *,
        limit: int,
        after_clip_id: str | None,
    ) -> list[VisualFingerprintRecord]:
        """Devuelve un lote ordenado por ``clip_id`` (estable para reanudación)."""

    def fetch_by_clip_id(self, session: Any, clip_id: str) -> VisualFingerprintRecord | None:
        """Un clip o None si no hay embedding visual indexado."""


class MultimodalRegenWorkUnitBatchPort(Protocol):
    """Lote enriquecido con facetas taxonómicas y vector para validación (un round-trip SQL)."""

    def fetch_work_units(
        self,
        session: Any,
        *,
        limit: int,
        after_clip_id: str | None,
    ) -> list[MultimodalRegenWorkUnit]:
        """Unidades listas para regenerar metadatos Chroma."""


class ChromaMultimodalWritePort(Protocol):
    """Escritura multimodal en el almacén vectorial (adaptador concreto)."""

    def upsert_multimodal(
        self,
        session: Any,
        payloads: list[ChromaFingerprintPayload],
        *,
        update_existing: bool,
    ) -> None:
        """Fusiona metadatos y opcionalmente embeddings según política de colección."""
