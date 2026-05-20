"""Tests de reglas de categoría editorial (Fase 6.7.X)."""

from aicos.domain.editorial_category.rules import (
    EDITORIAL_NARRATIVE_ROLES,
    auto_role_must_not_be_overwritten,
    effective_narrative_role,
    scene_type_label_for_role,
    should_persist_human_override,
)


def test_product_in_roles():
    assert "PRODUCT" in EDITORIAL_NARRATIVE_ROLES


def test_human_override_wins():
    assert effective_narrative_role("PROBLEM", "AUTHORITY") == "AUTHORITY"


def test_auto_used_when_no_human():
    assert effective_narrative_role("PROBLEM", None) == "PROBLEM"


def test_should_persist_when_different():
    assert should_persist_human_override("PROBLEM", "AUTHORITY") is True
    assert should_persist_human_override("PROBLEM", "PROBLEM") is False


def test_auto_immutable_once_set():
    assert auto_role_must_not_be_overwritten("PROBLEM", "HOOK") == "PROBLEM"


def test_product_label():
    assert scene_type_label_for_role("PRODUCT") == "Product Scene"
