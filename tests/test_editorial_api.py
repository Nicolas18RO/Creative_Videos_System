"""Tests HTTP del router editorial (SQLite aislado)."""

from __future__ import annotations

import uuid

import pytest

import aicos.config as cfgmod
import aicos.database.db as dbmod
from aicos.config import AppConfig, EditorialMetadataConfig, PathsConfig
from aicos.database.db import ClipRow, init_db, session_scope


@pytest.fixture
def editorial_client(tmp_path, monkeypatch):
    pytest.importorskip("fastapi")
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from aicos.api.routers import editorial_metadata as editorial_router

    db_path = tmp_path / "editorial_api.db"
    cfg = AppConfig(
        paths=PathsConfig(database=str(db_path)),
        editorial_metadata=EditorialMetadataConfig(enabled=True, persist_feedback=True),
    )
    monkeypatch.setattr(cfgmod, "_settings", cfg, raising=False)
    dbmod._engine = None
    dbmod._SessionLocal = None
    init_db()
    cid = str(uuid.uuid4())
    with session_scope() as session:
        session.add(
            ClipRow(
                id=cid,
                filename="t.mp4",
                relative_path="t.mp4",
                absolute_path=str(tmp_path / "t.mp4"),
            )
        )
    app = FastAPI()
    app.include_router(editorial_router.router, prefix="/editorial")
    client = TestClient(app)
    yield client, cid
    dbmod._engine = None
    dbmod._SessionLocal = None
    cfgmod._settings = None


def test_get_editorial_clip(editorial_client) -> None:
    client, cid = editorial_client
    r = client.get(f"/editorial/clips/{cid}")
    assert r.status_code == 200
    body = r.json()
    assert body["clip_id"] == cid


def test_patch_editorial_clip(editorial_client) -> None:
    client, cid = editorial_client
    r = client.patch(
        f"/editorial/clips/{cid}",
        json={"cinematic_score": 0.95, "editorial_tags": "macro, smoke"},
    )
    assert r.status_code == 200
    assert r.json()["cinematic_score"] == 0.95
    assert "macro" in r.json()["editorial_tags"]


def test_post_feedback(editorial_client) -> None:
    client, cid = editorial_client
    r = client.post(
        "/editorial/feedback",
        json={
            "clip_id": cid,
            "usefulness_score": 0.9,
            "continuity_score": 0.8,
            "diversity_score": 0.7,
            "narrative_quality": 0.85,
            "visual_quality": 0.8,
            "human_feedback": "muy útil",
        },
    )
    assert r.status_code == 200
    assert r.json()["clip_id"] == cid


def test_bulk_update(editorial_client) -> None:
    client, cid = editorial_client
    r = client.post(
        "/editorial/bulk-update",
        json={
            "items": [{"clip_id": cid, "patch": {"reviewed": True, "reviewed_by": "lead"}}],
            "corrected_by": "bulk",
            "correction_reason": "dataset",
        },
    )
    assert r.status_code == 200
    assert r.json()["updated"] == 1
