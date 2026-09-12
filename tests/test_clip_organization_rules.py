"""Fase 1: contrato de dominio de Clip Organization. Sin I/O de biblioteca real."""

from pathlib import Path

from aicos.domain.clip_organization.entities import (
    LibraryTaxonomy,
    OrganizationDecision,
    OrganizationInput,
)
from aicos.domain.clip_organization.rules import (
    build_organization_proposal,
    build_organized_filename,
    build_relative_folder,
    calculate_destination,
    destination_collides,
    is_safe_library_destination,
    is_safe_source_path,
    is_valid_library_taxonomy,
    organization_result_from_proposal,
)


def _tax(**overrides: object) -> LibraryTaxonomy:
    base = dict(
        gender="F",
        narrative_function="PROBLEM",
        subcategory="BACK_PAIN",
        context="POSTURE",
        variant=1,
        is_ai_generated=False,
    )
    base.update(overrides)
    return LibraryTaxonomy(**base)  # type: ignore[arg-type]


def _input(
    *,
    source: str = r"E:\tmp\incoming\clip.mp4",
    root: str = r"E:\tmp\library",
    current: LibraryTaxonomy | None = None,
    decision: LibraryTaxonomy | None = None,
    apply: bool = False,
    occupied: tuple[str, ...] = (),
    confidence: float | None = 0.91,
    reason: str = "filename heuristic",
) -> OrganizationInput:
    tax = decision or _tax()
    return OrganizationInput(
        source_path=source,
        library_root=root,
        current_taxonomy=current,
        decision=OrganizationDecision(
            taxonomy=tax,
            reason=reason,
            confidence=confidence,
            source="filename",
        ),
        apply=apply,
        clip_id="clip-1",
        occupied_destinations=occupied,
    )


def test_valid_organization_input_builds_eligible_proposal() -> None:
    proposal = build_organization_proposal(_input())
    assert proposal.eligible is True
    assert proposal.risk == "NONE"
    assert proposal.apply is False
    assert proposal.mode == "dry_run"
    assert proposal.action == "MOVE"
    assert proposal.proposed_filename == "F_PROBLEM_BACK_PAIN_POSTURE_01.mp4"
    assert proposal.proposed_relative_folder == "F/PROBLEM/BACK_PAIN/POSTURE"
    assert proposal.destination_path.replace("\\", "/").endswith(
        "library/F/PROBLEM/BACK_PAIN/POSTURE/F_PROBLEM_BACK_PAIN_POSTURE_01.mp4"
    )
    assert proposal.confidence == 0.91
    assert proposal.clip_id == "clip-1"


def test_invalid_taxonomy_rejected() -> None:
    assert is_valid_library_taxonomy(_tax(narrative_function="EMOTION")) is False
    assert is_valid_library_taxonomy(_tax(gender="X")) is False
    assert is_valid_library_taxonomy(_tax(subcategory="")) is False
    assert is_valid_library_taxonomy(_tax(variant=0)) is False
    assert is_valid_library_taxonomy(_tax(subcategory="../SECRET")) is False

    proposal = build_organization_proposal(_input(decision=_tax(narrative_function="NOT_A_ROLE")))
    assert proposal.eligible is False
    assert proposal.risk == "INVALID_TAXONOMY"
    assert proposal.action == "NONE"
    assert proposal.destination_path == ""


def test_destination_calculation_matches_taxonomy_axes() -> None:
    dest = calculate_destination(r"E:\tmp\library", _tax())
    assert dest == Path(r"E:\tmp\library") / "F" / "PROBLEM" / "BACK_PAIN" / "POSTURE" / (
        "F_PROBLEM_BACK_PAIN_POSTURE_01.mp4"
    )
    assert build_relative_folder(_tax(context=None)) == "F/PROBLEM/BACK_PAIN"


def test_destination_calculation_is_deterministic() -> None:
    a = calculate_destination(r"E:\tmp\library", _tax(gender="f", subcategory="back pain"))
    b = calculate_destination(r"E:\tmp\library", _tax(gender="F", subcategory="BACK_PAIN"))
    assert a == b
    p1 = build_organization_proposal(_input())
    p2 = build_organization_proposal(_input())
    assert p1.destination_path == p2.destination_path
    assert p1.proposed_filename == p2.proposed_filename


def test_filename_generation_matches_m4_convention() -> None:
    assert build_organized_filename(_tax()) == "F_PROBLEM_BACK_PAIN_POSTURE_01.mp4"
    assert (
        build_organized_filename(_tax(context=None, is_ai_generated=True, variant=3))
        == "F_PROBLEM_BACK_PAIN_IA_03.mp4"
    )
    assert build_organized_filename(_tax(context="NULL")) == "F_PROBLEM_BACK_PAIN_01.mp4"


def test_collision_detection_ignores_same_source() -> None:
    dest = str(calculate_destination(r"E:\tmp\library", _tax()))
    assert destination_collides(dest, source_path=dest, occupied_destinations=(dest,)) is False
    other = r"E:\tmp\incoming\other.mp4"
    assert destination_collides(dest, source_path=other, occupied_destinations=(dest,)) is True

    blocked = build_organization_proposal(_input(occupied=(dest,)))
    assert blocked.eligible is False
    assert blocked.risk == "COLLISION"
    assert blocked.action == "NONE"


def test_unsafe_path_rejection() -> None:
    assert is_safe_source_path("") is False
    assert is_safe_source_path(r"E:\tmp\incoming\..\outside.mp4") is False
    assert is_safe_source_path(r"E:\tmp\incoming\clip.mp4") is True

    root = r"E:\tmp\library"
    assert is_safe_library_destination(root, r"E:\tmp\library\F\PROBLEM\x.mp4") is True
    assert is_safe_library_destination(root, r"E:\tmp\other\F\PROBLEM\x.mp4") is False
    assert is_safe_library_destination(root, r"E:\tmp\library\..\outside\x.mp4") is False
    assert is_safe_library_destination("", r"E:\tmp\library\x.mp4") is False

    unsafe = build_organization_proposal(_input(source=r"E:\tmp\incoming\..\escape.mp4"))
    assert unsafe.eligible is False
    assert unsafe.risk == "UNSAFE"


def test_dry_run_vs_apply_does_not_execute_move() -> None:
    dry = organization_result_from_proposal(build_organization_proposal(_input(apply=False)))
    applied_intent = organization_result_from_proposal(build_organization_proposal(_input(apply=True)))
    assert dry.applied is False
    assert applied_intent.applied is False
    assert dry.proposal.mode == "dry_run"
    assert applied_intent.proposal.mode == "apply"
    assert "no se movió" in dry.message.lower() or "dry-run" in dry.message.lower()


def test_legacy_gender_is_canonicalized() -> None:
    tax = _tax(gender="NEUTRAL")
    assert is_valid_library_taxonomy(tax) is True
    assert build_organized_filename(tax).startswith("N_")
