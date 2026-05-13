"""Tests del parser de taxonomía."""

from __future__ import annotations

import pytest

from aicos.taxonomy.parser import parse_filename


@pytest.mark.parametrize(
    "name,exp_gender,exp_nf,exp_sub,exp_ctx,exp_var,exp_ai,compliant",
    [
        ("F_PROBLEM_KNEE_PAIN_STAIRS_01.mp4", "F", "PROBLEM", "KNEE_PAIN", "STAIRS", 1, False, True),
        ("M_HOOK_HAIR_PROBLEM_IA_01.mp4", "M", "HOOK", "HAIR_PROBLEM", None, 1, True, True),
        (
            "N_AUTHORITY_ANIMATION_KNEE_ANIMATION_IA_03.mp4",
            "N",
            "AUTHORITY",
            "ANIMATION",
            "KNEE_ANIMATION",
            3,
            True,
            True,
        ),
        (
            "MIX_BENEFIT_DAILY_ROUTINE_COUPLE_CONTEX_SLEEPING_01.mp4",
            "MIX",
            "BENEFIT",
            "DAILY_ROUTINE",
            "COUPLE_CONTEX_SLEEPING",
            1,
            False,
            True,
        ),
        ("M_RESULT_IDEAL_PHYSICAL_STATE_OLDMAN_04.mp4", "M", "RESULT", "IDEAL_PHYSICAL_STATE", "OLDMAN", 4, False, True),
        ("NEUTRAL_AUTHORITY_SPINE_3D_ANIMATION_01.mp4", "N", "AUTHORITY", "SPINE_3D", "ANIMATION", 1, False, False),
        ("KID_AUTHORITY_DEVELOPMENT_01.mp4", "KIDS", "AUTHORITY", "DEVELOPMENT", None, 1, False, False),
        ("clearzal pain relieving gel 03(12)-1.mp4", None, None, None, None, None, False, False),
        ("TEMPRORAL(1)-1.mp4", None, None, None, None, None, False, False),
        ("SE_CRYING_WOMEN_01.aac", None, None, "CRYING", "WOMEN", 1, False, True),
    ],
)
def test_parse_filename_param(
    name: str,
    exp_gender: str | None,
    exp_nf: str | None,
    exp_sub: str | None,
    exp_ctx: str | None,
    exp_var: int | None,
    exp_ai: bool,
    compliant: bool,
) -> None:
    t = parse_filename(name)
    assert t.gender == exp_gender
    assert t.narrative_function == exp_nf
    assert t.subcategory == exp_sub
    assert t.context == exp_ctx
    assert t.variant_number == exp_var
    assert t.is_ai_generated is exp_ai
    assert t.is_naming_compliant is compliant
