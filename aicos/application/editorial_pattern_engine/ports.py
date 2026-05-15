"""Puertos del motor 6.2 (Protocol): sin SQLAlchemy en contratos."""

from __future__ import annotations

from typing import Any, Protocol, Sequence, runtime_checkable

from aicos.domain.editorial_pattern_engine.entities import (
    ClipUsagePressureDigest,
    TimelineEnrichmentBundle,
)


@runtime_checkable
class TimelinePatternEnrichmentPort(Protocol):
    """Carga enriquecimiento Fase 5 + taxonomía de biblioteca por clip_id."""

    def load_bundle(self, session: Any, clip_ids: Sequence[str]) -> TimelineEnrichmentBundle:
        ...


@runtime_checkable
class ClipUsageHistoryDigestPort(Protocol):
    """Agrega presión histórica Fase 4 sobre clips del timeline."""

    def build_digest(self, session: Any, clip_ids: Sequence[str]) -> ClipUsagePressureDigest:
        ...
