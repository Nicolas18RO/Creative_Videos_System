"""Fase 4: sincronización SQLite tras organización. SQLite en memoria + tmp dirs."""

from __future__ import annotations

import uuid
from pathlib import Path

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker

from aicos.application.clip_organization.organization_execution_service import execute_organization
from aicos.application.clip_organization.organization_sync_service import (
    paths_are_consistent,
    sync_organized_clip,
)
from aicos.database.db import Base, ClipRow
from aicos.domain.clip_organization.entities import LibraryTaxonomy, OrganizationDecision


def _session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(engine, expire_on_commit=False)()


def _tax() -> LibraryTaxonomy:
    return LibraryTaxonomy(
        gender="F",
        narrative_function="PROBLEM",
        subcategory="BACK_PAIN",
        context="POSTURE",
        variant=1,
        is_ai_generated=False,
    )


def _decision() -> OrganizationDecision:
    return OrganizationDecision(taxonomy=_tax(), reason="test", confidence=0.9, source="filename")


def _seed_clip(session: Session, *, clip_id: str, absolute_path: str, relative_path: str, filename: str) -> ClipRow:
    row = ClipRow(
        id=clip_id,
        filename=filename,
        relative_path=relative_path,
        absolute_path=absolute_path,
        gender="F",
        narrative_function="PROBLEM",
        subcategory="BACK_PAIN",
        context=None,
        variant_number=1,
        is_ai_generated=False,
        asset_kind="video",
    )
    session.add(row)
    session.commit()
    return row


def test_successful_move_updates_same_clip_row(tmp_path: Path) -> None:
    incoming = tmp_path / "incoming"
    library = tmp_path / "library"
    incoming.mkdir()
    library.mkdir()
    source = incoming / "raw_clip.mp4"
    source.write_bytes(b"payload")
    clip_id = str(uuid.uuid4())
    session = _session()
    _seed_clip(
        session,
        clip_id=clip_id,
        absolute_path=str(source.resolve()),
        relative_path="incoming/raw_clip.mp4",
        filename="raw_clip.mp4",
    )

    execution = execute_organization(
        source_path=source,
        library_root=library,
        decision=_decision(),
        clip_id=clip_id,
    )
    assert execution.applied is True
    dest = Path(execution.destination_path or "")

    sync = sync_organized_clip(
        session,
        destination_path=dest,
        library_root=library,
        source_path=Path(execution.source_path),
        clip_id=clip_id,
    )
    session.commit()

    assert sync.synced is True
    assert sync.clip_id == clip_id
    row = session.get(ClipRow, clip_id)
    assert row is not None
    assert Path(row.absolute_path).resolve() == dest.resolve()
    assert row.filename == "F_PROBLEM_BACK_PAIN_POSTURE_01.mp4"
    assert paths_are_consistent(
        absolute_path=row.absolute_path,
        relative_path=row.relative_path,
        library_root=library,
        dest=dest,
    )
    stale = session.execute(select(ClipRow).where(ClipRow.absolute_path == str(source.resolve()))).scalar_one_or_none()
    assert stale is None
    assert session.execute(select(func.count()).select_from(ClipRow)).scalar_one() == 1


def test_failed_move_leaves_database_unchanged(tmp_path: Path) -> None:
    incoming = tmp_path / "incoming"
    library = tmp_path / "library"
    incoming.mkdir()
    library.mkdir()
    source = incoming / "raw_clip.mp4"
    source.write_bytes(b"src")
    dest = library / "F" / "PROBLEM" / "BACK_PAIN" / "POSTURE" / "F_PROBLEM_BACK_PAIN_POSTURE_01.mp4"
    dest.parent.mkdir(parents=True)
    dest.write_bytes(b"keep")
    clip_id = str(uuid.uuid4())
    session = _session()
    _seed_clip(
        session,
        clip_id=clip_id,
        absolute_path=str(source.resolve()),
        relative_path="incoming/raw_clip.mp4",
        filename="raw_clip.mp4",
    )

    execution = execute_organization(source_path=source, library_root=library, decision=_decision(), clip_id=clip_id)
    assert execution.applied is False

    if execution.applied:
        sync_organized_clip(
            session,
            destination_path=dest,
            library_root=library,
            source_path=source,
            clip_id=clip_id,
        )
        session.commit()

    row = session.get(ClipRow, clip_id)
    assert row is not None
    assert Path(row.absolute_path).resolve() == source.resolve()
    assert row.filename == "raw_clip.mp4"
    assert dest.read_bytes() == b"keep"


def test_sync_refuses_when_destination_missing(tmp_path: Path) -> None:
    library = tmp_path / "library"
    library.mkdir()
    missing = library / "F" / "PROBLEM" / "BACK_PAIN" / "POSTURE" / "F_PROBLEM_BACK_PAIN_POSTURE_01.mp4"
    incoming = tmp_path / "incoming"
    incoming.mkdir()
    source = incoming / "raw_clip.mp4"
    source.write_bytes(b"still-here")
    clip_id = str(uuid.uuid4())
    session = _session()
    _seed_clip(
        session,
        clip_id=clip_id,
        absolute_path=str(source.resolve()),
        relative_path="incoming/raw_clip.mp4",
        filename="raw_clip.mp4",
    )

    sync = sync_organized_clip(
        session,
        destination_path=missing,
        library_root=library,
        source_path=source,
        clip_id=clip_id,
    )
    session.commit()

    assert sync.synced is False
    row = session.get(ClipRow, clip_id)
    assert row is not None
    assert Path(row.absolute_path).resolve() == source.resolve()


def test_repeated_sync_keeps_single_row(tmp_path: Path) -> None:
    library = tmp_path / "library"
    folder = library / "F" / "PROBLEM" / "BACK_PAIN" / "POSTURE"
    folder.mkdir(parents=True)
    dest = folder / "F_PROBLEM_BACK_PAIN_POSTURE_01.mp4"
    dest.write_bytes(b"already")
    clip_id = str(uuid.uuid4())
    session = _session()
    _seed_clip(
        session,
        clip_id=clip_id,
        absolute_path=str(dest.resolve()),
        relative_path="F/PROBLEM/BACK_PAIN/POSTURE/F_PROBLEM_BACK_PAIN_POSTURE_01.mp4",
        filename=dest.name,
    )

    first = sync_organized_clip(session, destination_path=dest, library_root=library, source_path=dest, clip_id=clip_id)
    session.commit()
    second = sync_organized_clip(session, destination_path=dest, library_root=library, source_path=dest, clip_id=clip_id)
    session.commit()

    assert first.synced is True
    assert second.synced is True
    assert first.clip_id == second.clip_id == clip_id
    assert session.execute(select(func.count()).select_from(ClipRow)).scalar_one() == 1


def test_path_consistency_helper(tmp_path: Path) -> None:
    library = tmp_path / "library"
    dest = library / "F" / "PROBLEM" / "x.mp4"
    dest.parent.mkdir(parents=True)
    dest.write_bytes(b"x")
    rel = "F/PROBLEM/x.mp4"
    assert paths_are_consistent(
        absolute_path=str(dest.resolve()),
        relative_path=rel,
        library_root=library,
        dest=dest,
    )
    assert (
        paths_are_consistent(
            absolute_path=str(dest.resolve()),
            relative_path="wrong/path.mp4",
            library_root=library,
            dest=dest,
        )
        is False
    )
