"""Tests dominio registry editorial."""

from datetime import datetime, timezone

from aicos.domain.editorial_registry.entities import EditorialRegistrySession
from aicos.domain.editorial_registry.rules import detect_possible_duplicate, normalize_status_filter


def _entry(**kwargs) -> EditorialRegistrySession:
    now = datetime.now(timezone.utc)
    base = dict(
        session_id="s1",
        creative_id="cr_a",
        creative_label="Hook Producto X",
        project_label="P1",
        product_category="beauty",
        status="committed",
        committed_at=now,
        created_at=now,
        updated_at=now,
        scene_count=5,
        duration_seconds=30.0,
        has_feedback=True,
        has_timeline=True,
        notes="",
        corrections_count=1,
    )
    base.update(kwargs)
    return EditorialRegistrySession(**base)


def test_normalize_status_filter():
    assert normalize_status_filter("committed") == "committed"
    assert normalize_status_filter("ALL") is None
    assert normalize_status_filter("invalid") is None


def test_detect_duplicate_by_creative_id():
    entries = (_entry(creative_id="cr_a"), _entry(session_id="s2", creative_id="cr_b"))
    dupes = detect_possible_duplicate(entries, creative_id="cr_a", creative_label="")
    assert len(dupes) == 1
    assert dupes[0].session_id == "s1"


def test_detect_duplicate_by_label():
    entries = (_entry(creative_label="  Hook Producto X  "),)
    dupes = detect_possible_duplicate(entries, creative_id="", creative_label="hook producto x")
    assert len(dupes) == 1
