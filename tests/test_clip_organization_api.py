"""Fase 5: contrato HTTP de /organize. App mínima, SQLite memoria, tmp dirs."""

from __future__ import annotations

import uuid
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from aicos.api.routers import organize as organize_router
from aicos.database.db import Base, ClipRow


def _fake_config(library: Path, thumbs: Path) -> SimpleNamespace:
    return SimpleNamespace(
        runtime=SimpleNamespace(local_only=True),
        vision=SimpleNamespace(classification_confidence_threshold=0.75),
        ui=SimpleNamespace(thumbnail_size=(160, 90)),
        resolved_paths=lambda: {"library_root": library, "thumbnails_cache": thumbs},
    )


def _client(monkeypatch, tmp_path: Path) -> tuple[TestClient, object, Path, Path]:
    incoming = tmp_path / "incoming"
    library = tmp_path / "library"
    thumbs = tmp_path / "thumbs"
    incoming.mkdir()
    library.mkdir()
    thumbs.mkdir()

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(engine, expire_on_commit=False)

    @contextmanager
    def _scope():
        session = SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    monkeypatch.setattr(organize_router, "session_scope", _scope)
    monkeypatch.setattr(
        "aicos.modules.clip_organizer.get_config",
        lambda: _fake_config(library, thumbs),
    )

    class _SkipEmbedder:
        def __init__(self, *args: object, **kwargs: object) -> None:
            raise RuntimeError("vector index omitted in API tests")

    monkeypatch.setattr("aicos.modules.clip_organizer.Embedder", _SkipEmbedder)

    app = FastAPI()
    app.include_router(organize_router.router, prefix="/organize")
    return TestClient(app), SessionLocal, incoming, library


def test_invalid_request_requires_target(monkeypatch, tmp_path: Path) -> None:
    client, _, _, _ = _client(monkeypatch, tmp_path)
    r = client.post("/organize", json={"apply": False})
    assert r.status_code == 422


def test_missing_file_returns_400(monkeypatch, tmp_path: Path) -> None:
    client, _, incoming, _ = _client(monkeypatch, tmp_path)
    r = client.post("/organize", json={"video_path": str(incoming / "gone.mp4")})
    assert r.status_code == 400
    assert "no encontrado" in r.json()["detail"].lower()


def test_missing_clip_returns_404(monkeypatch, tmp_path: Path) -> None:
    client, _, _, _ = _client(monkeypatch, tmp_path)
    r = client.post("/organize", json={"clip_id": "missing-clip"})
    assert r.status_code == 404
    assert "clip_not_found" in r.json()["detail"]


def test_valid_dry_run(monkeypatch, tmp_path: Path) -> None:
    client, _, incoming, library = _client(monkeypatch, tmp_path)
    source = incoming / "F_PROBLEM_BACK_PAIN_POSTURE_01.mp4"
    source.write_bytes(b"video")

    r = client.post("/organize", json={"video_path": str(source)})
    assert r.status_code == 200
    body = r.json()
    assert body["applied"] is False
    assert body["risk"] == "NONE"
    assert body["eligible"] is True
    assert body["action"] == "MOVE"
    assert body["proposed_filename"] == "F_PROBLEM_BACK_PAIN_POSTURE_01.mp4"
    assert body["destination_path"]
    assert source.is_file()
    dest = Path(body["destination_path"])
    assert dest.exists() is False
    assert dest.is_relative_to(library) or str(library) in dest.as_posix() or str(library) in str(dest)


def test_successful_apply_moves_and_syncs_db(monkeypatch, tmp_path: Path) -> None:
    client, SessionLocal, incoming, library = _client(monkeypatch, tmp_path)
    source = incoming / "F_PROBLEM_BACK_PAIN_POSTURE_01.mp4"
    source.write_bytes(b"payload")
    clip_id = str(uuid.uuid4())
    with SessionLocal() as session:
        session.add(
            ClipRow(
                id=clip_id,
                filename=source.name,
                relative_path="incoming/F_PROBLEM_BACK_PAIN_POSTURE_01.mp4",
                absolute_path=str(source.resolve()),
                gender="F",
                narrative_function="PROBLEM",
                subcategory="BACK_PAIN",
                context="POSTURE",
                variant_number=1,
                asset_kind="video",
            )
        )
        session.commit()

    r = client.post("/organize", json={"video_path": str(source), "clip_id": clip_id, "apply": True})
    assert r.status_code == 200
    body = r.json()
    assert body["applied"] is True
    assert body["risk"] == "NONE"
    dest = Path(body["destination_path"])
    assert dest.is_file()
    assert dest.read_bytes() == b"payload"
    assert source.exists() is False
    with SessionLocal() as session:
        row = session.get(ClipRow, clip_id)
        assert row is not None
        assert Path(row.absolute_path).resolve() == dest.resolve()
        stale = session.execute(
            select(ClipRow).where(ClipRow.absolute_path == str(source.resolve()))
        ).scalar_one_or_none()
        assert stale is None


def test_inbound_decision_overrides_filename_heuristic(monkeypatch, tmp_path: Path) -> None:
    client, _, incoming, library = _client(monkeypatch, tmp_path)
    source = incoming / "F_PROBLEM_BACK_PAIN_POSTURE_01.mp4"
    source.write_bytes(b"video")

    r = client.post(
        "/organize",
        json={
            "video_path": str(source),
            "decision": {
                "gender": "M",
                "narrative_function": "HOOK",
                "subcategory": "OPENER",
                "variant": 2,
                "source": "model",
                "confidence": 0.2,
                "provenance_model": "future-engine",
                "provenance_version": "9",
            },
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["applied"] is False
    assert body["eligible"] is True
    assert body["proposed_filename"] == "M_HOOK_OPENER_02.mp4"
    dest = Path(body["destination_path"])
    assert dest == library / "M" / "HOOK" / "OPENER" / "M_HOOK_OPENER_02.mp4"
    assert dest.exists() is False
    assert source.is_file()
    assert "future-engine" not in body["destination_path"]
    assert body["classification"]["gender"] == "M"


def test_apply_collision_returns_409(monkeypatch, tmp_path: Path) -> None:
    client, _, incoming, library = _client(monkeypatch, tmp_path)
    source = incoming / "F_PROBLEM_BACK_PAIN_POSTURE_01.mp4"
    source.write_bytes(b"src")
    dest = library / "F" / "PROBLEM" / "BACK_PAIN" / "POSTURE" / "F_PROBLEM_BACK_PAIN_POSTURE_01.mp4"
    dest.parent.mkdir(parents=True)
    dest.write_bytes(b"keep")

    r = client.post("/organize", json={"video_path": str(source), "apply": True})
    assert r.status_code == 409
    body = r.json()
    assert body["applied"] is False
    assert body["risk"] == "COLLISION"
    assert dest.read_bytes() == b"keep"
    assert source.read_bytes() == b"src"
