"""Presentación API del registry editorial."""

from __future__ import annotations

from aicos.domain.editorial_registry.entities import EditorialRegistrySession, EditorialRegistrySummary
from aicos.models.schemas import EditorialRegistrySessionOut, EditorialRegistrySummaryOut


def session_to_out(s: EditorialRegistrySession) -> EditorialRegistrySessionOut:
    return EditorialRegistrySessionOut(
        session_id=s.session_id,
        creative_id=s.creative_id,
        creative_label=s.creative_label,
        project_label=s.project_label,
        product_category=s.product_category,
        status=s.status,
        committed_at=s.committed_at.isoformat() if s.committed_at else None,
        created_at=s.created_at.isoformat(),
        updated_at=s.updated_at.isoformat(),
        scene_count=s.scene_count,
        duration_seconds=s.duration_seconds,
        has_feedback=s.has_feedback,
        has_timeline=s.has_timeline,
        notes=s.notes,
        corrections_count=s.corrections_count,
    )


def summary_to_out(s: EditorialRegistrySummary) -> EditorialRegistrySummaryOut:
    return EditorialRegistrySummaryOut(
        total=s.total,
        committed=s.committed,
        awaiting_human=s.awaiting_human,
        analyzing=s.analyzing,
        failed=s.failed,
        draft=s.draft,
        ready=s.ready,
        with_timeline=s.with_timeline,
        with_feedback=s.with_feedback,
    )
