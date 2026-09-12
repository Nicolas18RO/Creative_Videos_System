"""Fase 3: ejecución segura de filesystem. Solo directorios temporales."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from aicos.application.clip_organization.organization_execution_service import execute_organization
from aicos.domain.clip_organization.entities import LibraryTaxonomy, OrganizationDecision
from aicos.modules.clip_organizer import organize_clip


def _tax(**overrides: object) -> LibraryTaxonomy:
    base: dict[str, object] = dict(
        gender="F",
        narrative_function="PROBLEM",
        subcategory="BACK_PAIN",
        context="POSTURE",
        variant=1,
        is_ai_generated=False,
    )
    base.update(overrides)
    return LibraryTaxonomy(**base)  # type: ignore[arg-type]


def _decision(tax: LibraryTaxonomy | None = None) -> OrganizationDecision:
    return OrganizationDecision(
        taxonomy=tax or _tax(),
        reason="test",
        confidence=0.9,
        source="filename",
    )


def test_successful_move(tmp_path: Path) -> None:
    incoming = tmp_path / "incoming"
    library = tmp_path / "library"
    incoming.mkdir()
    library.mkdir()
    source = incoming / "raw_clip.mp4"
    source.write_bytes(b"payload")

    result = execute_organization(source_path=source, library_root=library, decision=_decision())

    dest = library / "F" / "PROBLEM" / "BACK_PAIN" / "POSTURE" / "F_PROBLEM_BACK_PAIN_POSTURE_01.mp4"
    assert result.applied is True
    assert result.risk == "NONE"
    assert dest.is_file()
    assert dest.read_bytes() == b"payload"
    assert source.exists() is False


def test_successful_rename(tmp_path: Path) -> None:
    library = tmp_path / "library"
    folder = library / "F" / "PROBLEM" / "BACK_PAIN" / "POSTURE"
    folder.mkdir(parents=True)
    source = folder / "old_name.mp4"
    source.write_bytes(b"renamed")

    result = execute_organization(source_path=source, library_root=library, decision=_decision())

    dest = folder / "F_PROBLEM_BACK_PAIN_POSTURE_01.mp4"
    assert result.applied is True
    assert dest.is_file()
    assert dest.read_bytes() == b"renamed"
    assert source.exists() is False


def test_missing_source(tmp_path: Path) -> None:
    library = tmp_path / "library"
    library.mkdir()
    missing = tmp_path / "incoming" / "gone.mp4"

    result = execute_organization(source_path=missing, library_root=library, decision=_decision())

    assert result.applied is False
    assert result.risk == "INVALID"
    assert list(library.rglob("*.mp4")) == []


def test_destination_collision_does_not_overwrite(tmp_path: Path) -> None:
    incoming = tmp_path / "incoming"
    library = tmp_path / "library"
    incoming.mkdir()
    library.mkdir()
    source = incoming / "raw_clip.mp4"
    source.write_bytes(b"src")
    dest = library / "F" / "PROBLEM" / "BACK_PAIN" / "POSTURE" / "F_PROBLEM_BACK_PAIN_POSTURE_01.mp4"
    dest.parent.mkdir(parents=True)
    dest.write_bytes(b"keep-me")

    result = execute_organization(source_path=source, library_root=library, decision=_decision())

    assert result.applied is False
    assert result.risk == "COLLISION"
    assert dest.read_bytes() == b"keep-me"
    assert source.read_bytes() == b"src"


def test_invalid_library_root(tmp_path: Path) -> None:
    incoming = tmp_path / "incoming"
    incoming.mkdir()
    source = incoming / "raw_clip.mp4"
    source.write_bytes(b"video")
    not_a_dir = tmp_path / "library_file"
    not_a_dir.write_text("nope", encoding="utf-8")

    result = execute_organization(source_path=source, library_root=not_a_dir, decision=_decision())

    assert result.applied is False
    assert result.risk == "INVALID"
    assert source.is_file()


def test_move_oserror_is_not_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    incoming = tmp_path / "incoming"
    library = tmp_path / "library"
    incoming.mkdir()
    library.mkdir()
    source = incoming / "raw_clip.mp4"
    source.write_bytes(b"video")

    def _boom(src: str, dst: str) -> None:
        raise OSError("simulated permission error")

    monkeypatch.setattr(
        "aicos.application.clip_organization.organization_execution_service.shutil.move",
        _boom,
    )
    result = execute_organization(source_path=source, library_root=library, decision=_decision())

    assert result.applied is False
    assert "no se pudo mover" in result.message.lower()
    assert source.is_file()
    dest = library / "F" / "PROBLEM" / "BACK_PAIN" / "POSTURE" / "F_PROBLEM_BACK_PAIN_POSTURE_01.mp4"
    assert dest.exists() is False


def test_no_false_success_if_destination_missing_after_move(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    incoming = tmp_path / "incoming"
    library = tmp_path / "library"
    incoming.mkdir()
    library.mkdir()
    source = incoming / "raw_clip.mp4"
    source.write_bytes(b"video")

    def _lie(src: str, dst: str) -> None:
        return None

    monkeypatch.setattr(
        "aicos.application.clip_organization.organization_execution_service.shutil.move",
        _lie,
    )
    result = execute_organization(source_path=source, library_root=library, decision=_decision())

    assert result.applied is False
    assert "no se pudo verificar" in result.message.lower()
    assert source.is_file()


def test_post_move_verification(tmp_path: Path) -> None:
    incoming = tmp_path / "incoming"
    library = tmp_path / "library"
    incoming.mkdir()
    library.mkdir()
    source = incoming / "raw_clip.mp4"
    source.write_bytes(b"verify")

    result = execute_organization(source_path=source, library_root=library, decision=_decision())
    dest = Path(result.destination_path or "")

    assert result.applied is True
    assert dest.is_file()
    assert dest.stat().st_size == 6
    assert source.exists() is False


@pytest.mark.asyncio
async def test_organize_clip_apply_collision_does_not_index(tmp_path: Path) -> None:
    incoming = tmp_path / "incoming"
    library = tmp_path / "library"
    incoming.mkdir()
    library.mkdir()
    source = incoming / "F_PROBLEM_BACK_PAIN_POSTURE_01.mp4"
    source.write_bytes(b"src")
    dest = library / "F" / "PROBLEM" / "BACK_PAIN" / "POSTURE" / "F_PROBLEM_BACK_PAIN_POSTURE_01.mp4"
    dest.parent.mkdir(parents=True)
    dest.write_bytes(b"keep")

    response = await organize_clip(source, apply=True, session=MagicMock(), library_root=library)

    assert response.applied is False
    assert response.indexed is False
    assert response.risk == "COLLISION"
    assert dest.read_bytes() == b"keep"
    assert source.read_bytes() == b"src"
