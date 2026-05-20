"""Tests aplicación registry editorial."""

from datetime import datetime, timezone

from aicos.application.editorial_registry.editorial_registry_service import EditorialRegistryService
from aicos.domain.editorial_registry.entities import EditorialRegistrySession


class _MemRegistry:
    def __init__(self, rows):
        self._rows = rows

    def list_sessions(self, session, *, status=None):
        if status:
            return tuple(r for r in self._rows if r.status == status)
        return self._rows


def _row(status: str, product: str = "beauty") -> EditorialRegistrySession:
    now = datetime.now(timezone.utc)
    return EditorialRegistrySession(
        session_id=f"s-{status}",
        creative_id=f"cr-{status}",
        creative_label=f"label-{status}",
        project_label="proj",
        product_category=product,
        status=status,
        committed_at=now if status == "committed" else None,
        created_at=now,
        updated_at=now,
        scene_count=3,
        duration_seconds=12.0,
        has_feedback=status == "committed",
        has_timeline=True,
        notes="",
        corrections_count=0,
    )


def test_list_committed_first():
    rows = (_row("awaiting_human"), _row("committed"))
    svc = EditorialRegistryService(registry_read=_MemRegistry(rows))
    out = svc.list_sessions(None)
    assert out[0].status == "committed"


def test_filter_product_category():
    rows = (_row("committed", "beauty"), _row("committed", "tech"))
    svc = EditorialRegistryService(registry_read=_MemRegistry(rows))
    out = svc.list_sessions(None, product_category="tech")
    assert len(out) == 1
    assert out[0].product_category == "tech"


def test_summary_counts():
    rows = (_row("committed"), _row("failed"), _row("analyzing"))
    svc = EditorialRegistryService(registry_read=_MemRegistry(rows))
    s = svc.get_summary(None)
    assert s.total == 3
    assert s.committed == 1
    assert s.failed == 1
