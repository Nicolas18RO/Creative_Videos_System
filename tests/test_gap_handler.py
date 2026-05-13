"""Tests del clasificador de gaps."""

from aicos.models.schemas import Scene
from aicos.modules import gap_handler


def test_classify_gap_authority() -> None:
    s = Scene(
        scene_id="1",
        scene_index=0,
        start_ms=5000,
        end_ms=7000,
        duration_ms=2000,
        text="estudio clínico demuestra eficacia",
        concept="clinical study animation",
        narrative_function="AUTHORITY",
    )
    assert gap_handler.classify_gap_type(s) in ("both", "ai_generation", "tiktok_search")


def test_classify_gap_tiktok_default() -> None:
    s = Scene(
        scene_id="2",
        scene_index=1,
        start_ms=2000,
        end_ms=4000,
        duration_ms=2000,
        text="caminar por el parque",
        concept="walking park",
        narrative_function="BENEFIT",
    )
    assert gap_handler.classify_gap_type(s) == "tiktok_search"
