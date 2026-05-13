"""Smoke tests para /decisions (Fase 4)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from aicos.api.main import app


def test_decisions_endpoints_smoke() -> None:
    c = TestClient(app)
    r = c.get("/decisions/summary")
    assert r.status_code == 200
    body = r.json()
    assert "system_decision_score" in body
    assert "total_active_decisions" in body
    assert "high_severity_count" in body
    assert "decision_distribution" in body

    r2 = c.get("/decisions/list", params={"limit": 10, "offset": 0})
    assert r2.status_code == 200
    lst = r2.json()
    assert "items" in lst and "total" in lst

    r3 = c.get("/decisions/impact")
    assert r3.status_code == 200
    imp = r3.json()
    assert "most_affected_system_areas" in imp
