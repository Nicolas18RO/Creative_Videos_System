"""Smoke tests Fase 3 PRD: hooks, benchmark, reclasificación."""

from __future__ import annotations

from fastapi.testclient import TestClient

from aicos.api.main import app


def test_hooks_search_and_benchmark_smoke() -> None:
    c = TestClient(app)
    r = c.get("/hooks/search", params={"q": "woman pain knee stairs", "n_results": 3})
    assert r.status_code == 200
    assert "results" in r.json()

    b = c.get("/benchmark/phase3", params={"k": 3, "max_cases": 5})
    assert b.status_code == 200
    body = b.json()
    assert "baseline_precision_at_k" in body
    assert "enhanced_precision_at_k" in body


def test_reclassify_batch_smoke() -> None:
    c = TestClient(app)
    r = c.post("/taxonomy/reclassify/batch", json={"limit": 2, "include_export_file": False, "use_db_flagged": True})
    assert r.status_code == 200
    assert "suggestions" in r.json()
