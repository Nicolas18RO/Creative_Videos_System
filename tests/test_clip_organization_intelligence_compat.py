"""Fase 7: M4 consume una decisión portable. No implementa Clip Intelligence."""

from __future__ import annotations

from pathlib import Path

import pytest

from aicos.application.clip_organization.classification_adapter import (
    decision_from_inbound,
    incoming_signal_from_body,
    incoming_signal_from_classification,
    vision_classification_from_decision,
)
from aicos.domain.clip_organization.entities import IncomingOrganizationSignal, LibraryTaxonomy
from aicos.domain.clip_organization.rules import (
    build_organization_proposal,
    build_organized_filename,
    calculate_destination,
    normalize_decision_source,
    organization_decision_from_inbound,
)
from aicos.models.schemas import OrganizationDecisionBody, VisionClassification
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


def _signal(*, source: str, provenance_model: str | None = None, provenance_version: str | None = None):
    return IncomingOrganizationSignal(
        taxonomy=_tax(),
        confidence=0.91,
        source=source,
        reason="test inbound",
        provenance_model=provenance_model,
        provenance_version=provenance_version,
    )


def test_normalize_decision_source_is_portable() -> None:
    assert normalize_decision_source("filename") == "filename"
    assert normalize_decision_source("vision") == "filename"
    assert normalize_decision_source("human") == "human"
    assert normalize_decision_source("review") == "human"
    assert normalize_decision_source("model") == "model"
    assert normalize_decision_source("clip_intelligence") == "model"
    assert normalize_decision_source("unknown-engine") == "model"
    assert normalize_decision_source(None) == "unknown"


def test_inbound_strips_model_provenance() -> None:
    decision = organization_decision_from_inbound(
        _signal(source="model", provenance_model="future-engine", provenance_version="9.9")
    )
    assert decision.source == "model"
    assert decision.taxonomy == _tax()
    assert not hasattr(decision, "provenance_model")
    assert not hasattr(decision, "provenance_version")


def test_same_taxonomy_same_destination_regardless_of_source(tmp_path: Path) -> None:
    root = tmp_path / "library"
    expected = calculate_destination(str(root), _tax())
    filename = build_organized_filename(_tax())
    for source, model, version in (
        ("filename", None, None),
        ("human", None, None),
        ("model", "future-engine", "3.1"),
        ("clip_intelligence", "other-engine", "0.1"),
    ):
        decision = organization_decision_from_inbound(
            _signal(source=source, provenance_model=model, provenance_version=version)
        )
        dest = calculate_destination(str(root), decision.taxonomy)
        assert dest == expected
        assert build_organized_filename(decision.taxonomy) == filename


def test_proposal_ignores_provenance_fields(tmp_path: Path) -> None:
    from aicos.domain.clip_organization.entities import OrganizationDecision, OrganizationInput

    root = str(tmp_path / "library")
    source = str(tmp_path / "incoming" / "clip.mp4")
    human = build_organization_proposal(
        OrganizationInput(
            source_path=source,
            library_root=root,
            current_taxonomy=None,
            decision=OrganizationDecision(taxonomy=_tax(), source="human", confidence=0.98),
        )
    )
    model = build_organization_proposal(
        OrganizationInput(
            source_path=source,
            library_root=root,
            current_taxonomy=None,
            decision=organization_decision_from_inbound(
                _signal(source="model", provenance_model="future-engine", provenance_version="2")
            ),
        )
    )
    assert human.destination_path == model.destination_path
    assert human.proposed_filename == model.proposed_filename
    assert human.proposed_relative_folder == model.proposed_relative_folder


def test_adapter_body_keeps_taxonomy_and_drops_engine_name() -> None:
    body = OrganizationDecisionBody(
        gender="M",
        narrative_function="HOOK",
        subcategory="OPENER",
        context=None,
        variant=2,
        source="model",
        confidence=0.77,
        provenance_model="should-not-affect-path",
        provenance_version="x",
    )
    signal = incoming_signal_from_body(body)
    decision = decision_from_inbound(signal)
    assert decision.source == "model"
    dest = calculate_destination(r"E:\tmp\library", decision.taxonomy)
    assert dest.as_posix().endswith("library/M/HOOK/OPENER/M_HOOK_OPENER_02.mp4")
    assert "should-not-affect-path" not in dest.as_posix()


def test_adapter_from_classification_uses_filename_source() -> None:
    classification = VisionClassification(
        gender="F",
        narrative_function="PROBLEM",
        subcategory="BACK_PAIN",
        context="POSTURE",
        suggested_filename="ignored.mp4",
        suggested_folder="ignored/",
        confidence=0.88,
    )
    signal = incoming_signal_from_classification(
        classification,
        source_name="F_PROBLEM_BACK_PAIN_POSTURE_03.mp4",
        source="filename_heuristic",
    )
    decision = decision_from_inbound(signal)
    assert decision.source == "filename"
    assert decision.taxonomy.variant == 3
    assert vision_classification_from_decision(decision).tags == ["filename"]


def test_invalid_inbound_taxonomy_is_rejected(tmp_path: Path) -> None:
    from aicos.application.clip_organization.organization_preview_service import preview_organization

    incoming = tmp_path / "incoming"
    library = tmp_path / "library"
    incoming.mkdir()
    library.mkdir()
    source = incoming / "clip.mp4"
    source.write_bytes(b"video")
    decision = organization_decision_from_inbound(
        IncomingOrganizationSignal(
            taxonomy=_tax(narrative_function="NOT_A_FUNCTION"),
            source="model",
            provenance_model="future-engine",
        )
    )
    result = preview_organization(source_path=source, library_root=library, decision=decision)
    assert result.applied is False
    assert result.proposal.eligible is False
    assert result.risk == "INVALID_TAXONOMY"
    assert source.is_file()


@pytest.mark.asyncio
async def test_organize_clip_inbound_skips_filename_heuristic(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    incoming = tmp_path / "incoming"
    library = tmp_path / "library"
    incoming.mkdir()
    library.mkdir()
    source = incoming / "F_PROBLEM_BACK_PAIN_POSTURE_01.mp4"
    source.write_bytes(b"video")

    def _boom(_path: Path):
        raise AssertionError("M4 no debe clasificar si hay decisión inbound")

    monkeypatch.setattr(
        "aicos.modules.clip_organizer.vision_service.classify_from_path_heuristic",
        _boom,
    )

    response = await organize_clip(
        source,
        apply=False,
        library_root=library,
        inbound_signal=IncomingOrganizationSignal(
            taxonomy=_tax(gender="M", narrative_function="HOOK", subcategory="OPENER", context=None),
            confidence=0.12,
            source="human",
            reason="review",
            provenance_model="future-engine",
            provenance_version="1",
        ),
    )
    assert response.applied is False
    assert response.eligible is True
    assert response.proposed_filename == "M_HOOK_OPENER_01.mp4"
    assert response.destination_path
    dest = Path(response.destination_path)
    assert dest == library / "M" / "HOOK" / "OPENER" / "M_HOOK_OPENER_01.mp4"
    assert dest.exists() is False
    assert source.is_file()
    assert "future-engine" not in (response.destination_path or "")
    assert response.classification.gender == "M"
    assert response.classification.tags == ["human"]
