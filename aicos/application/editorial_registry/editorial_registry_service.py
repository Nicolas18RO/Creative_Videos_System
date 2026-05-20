"""Servicio de consulta del registry de sesiones (Fase 6.7.1)."""

from __future__ import annotations

import logging
from typing import Any

from aicos.application.editorial_registry.ports import EditorialRegistryReadPort
from aicos.domain.editorial_registry.entities import EditorialRegistrySession, EditorialRegistrySummary
from aicos.domain.editorial_registry.rules import (
    detect_possible_duplicate,
    normalize_status_filter,
    sort_registry_entries,
)
from aicos.domain.editorial_training.entities import EditorialTrainingSessionStatus

logger = logging.getLogger(__name__)


class EditorialRegistryService:
    def __init__(self, *, registry_read: EditorialRegistryReadPort) -> None:
        self._read = registry_read

    def list_sessions(
        self,
        session: Any,
        *,
        status: str | None = None,
        product_category: str | None = None,
    ) -> tuple[EditorialRegistrySession, ...]:
        norm = normalize_status_filter(status)
        rows = self._read.list_sessions(session, status=norm)
        if product_category:
            pc = product_category.strip().lower()
            rows = tuple(r for r in rows if (r.product_category or "").strip().lower() == pc)
        out = sort_registry_entries(rows, committed_first=True)
        logger.info("[EditorialRegistry] list_sessions count=%s status=%s", len(out), norm or "all")
        return out

    def get_summary(self, session: Any) -> EditorialRegistrySummary:
        rows = self._read.list_sessions(session, status=None)
        def _n(st: str) -> int:
            return sum(1 for r in rows if r.status == st)

        return EditorialRegistrySummary(
            total=len(rows),
            committed=_n(EditorialTrainingSessionStatus.COMMITTED),
            awaiting_human=_n(EditorialTrainingSessionStatus.AWAITING_HUMAN),
            analyzing=_n(EditorialTrainingSessionStatus.ANALYZING),
            failed=_n(EditorialTrainingSessionStatus.FAILED),
            draft=_n(EditorialTrainingSessionStatus.DRAFT),
            ready=_n(EditorialTrainingSessionStatus.READY),
            with_timeline=sum(1 for r in rows if r.has_timeline),
            with_feedback=sum(1 for r in rows if r.has_feedback),
        )

    def check_duplicates(
        self,
        session: Any,
        *,
        creative_id: str,
        creative_label: str,
    ) -> tuple[EditorialRegistrySession, ...]:
        rows = self._read.list_sessions(session, status=None)
        dupes = detect_possible_duplicate(rows, creative_id=creative_id, creative_label=creative_label)
        if dupes:
            logger.info(
                "[EditorialRegistry] duplicate_check creative_id=%s label=%s matches=%s",
                creative_id,
                creative_label,
                len(dupes),
            )
        return dupes
