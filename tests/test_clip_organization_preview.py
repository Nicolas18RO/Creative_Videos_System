"""Fase 2: dry-run de organización. Usa directorios temporales, nunca la biblioteca real."""

from __future__ import annotations

from pathlib import Path

import pytest

from aicos.application.clip_organization.organization_preview_service import (
    preview_organization,
)
from aicos.domain.clip_organization.entities import LibraryTaxonomy, OrganizationDecision
from aicos.modules.clip_organizer import organize_clip


def _snapshot(root: Path) -> dict[str, tuple[int, int]]:
    out: dict[str, tuple[int, int]] = {}
    if not root.exists():
        return out
    for p in root.rglob("*"):
        if p.is_file():
            st = p.stat()
            out[str(p.relative_to(root)).replace("\\", "/")] = (st.st_size, st.st_mtime_ns)
    return out


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


def test_preview_correct_destination_and_filename(tmp_path: Path) -> None:
    incoming = tmp_path / "incoming"
    library = tmp_path / "library"
    incoming.mkdir()
    library.mkdir()
    source = incoming / "raw_clip.mp4"
    source.write_bytes(b"video")

    result = preview_organization(
        source_path=source,
        library_root=library,
        decision=_decision(),
    )
    dest = Path(result.destination_path or "")
    assert result.applied is False
    assert result.risk == "NONE"
    assert result.proposal.proposed_filename == "F_PROBLEM_BACK_PAIN_POSTURE_01.mp4"
    assert dest == library / "F" / "PROBLEM" / "BACK_PAIN" / "POSTURE" / (
        "F_PROBLEM_BACK_PAIN_POSTURE_01.mp4"
    )
    assert dest.exists() is False
    assert source.is_file()


def test_preview_collision(tmp_path: Path) -> None:
    incoming = tmp_path / "incoming"
    library = tmp_path / "library"
    incoming.mkdir()
    library.mkdir()
    source = incoming / "raw_clip.mp4"
    source.write_bytes(b"src")
    dest = library / "F" / "PROBLEM" / "BACK_PAIN" / "POSTURE" / "F_PROBLEM_BACK_PAIN_POSTURE_01.mp4"
    dest.parent.mkdir(parents=True)
    dest.write_bytes(b"existing")

    result = preview_organization(
        source_path=source,
        library_root=library,
        decision=_decision(),
    )
    assert result.applied is False
    assert result.risk == "COLLISION"
    assert result.proposal.eligible is False
    assert dest.read_bytes() == b"existing"
    assert source.read_bytes() == b"src"


def test_preview_missing_source(tmp_path: Path) -> None:
    library = tmp_path / "library"
    library.mkdir()
    missing = tmp_path / "incoming" / "gone.mp4"

    result = preview_organization(
        source_path=missing,
        library_root=library,
        decision=_decision(),
    )
    assert result.applied is False
    assert result.risk == "INVALID"
    assert "origen" in result.proposal.reason.lower()
    assert list(library.rglob("*")) == []


def test_preview_invalid_destination(tmp_path: Path) -> None:
    incoming = tmp_path / "incoming"
    incoming.mkdir()
    source = incoming / "raw_clip.mp4"
    source.write_bytes(b"video")
    not_a_dir = tmp_path / "library_file"
    not_a_dir.write_text("nope", encoding="utf-8")

    result = preview_organization(
        source_path=source,
        library_root=not_a_dir,
        decision=_decision(),
    )
    assert result.applied is False
    assert result.risk == "INVALID"
    assert "destino" in result.proposal.reason.lower()
    assert source.is_file()
    assert not_a_dir.is_file()


def test_preview_is_deterministic(tmp_path: Path) -> None:
    incoming = tmp_path / "incoming"
    library = tmp_path / "library"
    incoming.mkdir()
    library.mkdir()
    source = incoming / "raw_clip.mp4"
    source.write_bytes(b"video")

    first = preview_organization(source_path=source, library_root=library, decision=_decision())
    second = preview_organization(source_path=source, library_root=library, decision=_decision())
    assert first.destination_path == second.destination_path
    assert first.proposal.proposed_filename == second.proposal.proposed_filename
    assert first.risk == second.risk
    assert first.proposal.action == second.proposal.action


def test_preview_leaves_filesystem_unchanged(tmp_path: Path) -> None:
    incoming = tmp_path / "incoming"
    library = tmp_path / "library"
    incoming.mkdir()
    library.mkdir()
    source = incoming / "raw_clip.mp4"
    source.write_bytes(b"video")
    extra = library / "keep.txt"
    extra.write_text("stay", encoding="utf-8")
    before = _snapshot(tmp_path)

    preview_organization(source_path=source, library_root=library, decision=_decision())

    assert _snapshot(tmp_path) == before


@pytest.mark.asyncio
async def test_organize_clip_dry_run_does_not_move(tmp_path: Path) -> None:
    incoming = tmp_path / "incoming"
    library = tmp_path / "library"
    incoming.mkdir()
    library.mkdir()
    source = incoming / "F_PROBLEM_BACK_PAIN_POSTURE_01.mp4"
    source.write_bytes(b"video")
    before = _snapshot(tmp_path)

    response = await organize_clip(source, apply=False, library_root=library)

    assert response.applied is False
    assert response.indexed is False
    assert response.proposed_filename == "F_PROBLEM_BACK_PAIN_POSTURE_01.mp4"
    assert response.risk == "NONE"
    assert response.destination_path is not None
    assert Path(response.destination_path) == library / "F" / "PROBLEM" / "BACK_PAIN" / "POSTURE" / (
        "F_PROBLEM_BACK_PAIN_POSTURE_01.mp4"
    )
    assert source.is_file()
    assert _snapshot(tmp_path) == before
