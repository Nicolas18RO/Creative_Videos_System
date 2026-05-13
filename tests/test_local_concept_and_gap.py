"""Extracción de concepto y gaps locales (sin OpenAI)."""

from __future__ import annotations

import pytest

from aicos.core import concept_extractor
from aicos.core.local_ai.concept_local import extract_concept_local
from aicos.core.local_ai.gap_local import generate_tiktok_keywords_local
from aicos.models.schemas import Scene, SearchResponse
from aicos.modules import gap_handler


def test_extract_concept_local_domain_map() -> None:
    out = extract_concept_local("dolor de rodilla al subir escaleras", "PROBLEM")
    assert isinstance(out, str)
    assert len(out) > 0


@pytest.mark.asyncio
async def test_extract_concept_async_ignores_llm() -> None:
    out = await concept_extractor.extract_concept("problema digestivo leve", "PROBLEM", llm=object())
    assert isinstance(out, str)


def test_tiktok_keywords_local() -> None:
    s = Scene(
        scene_id="x",
        scene_index=0,
        start_ms=0,
        end_ms=1000,
        duration_ms=1000,
        text="test",
        concept="knee pain relief",
        narrative_function="BENEFIT",
    )
    kws = generate_tiktok_keywords_local(s, product_category="salud", target_audience="adultos")
    assert len(kws) >= 4
    assert all(isinstance(k, str) for k in kws)


@pytest.mark.asyncio
async def test_enrich_gap_local_no_llm() -> None:
    s = Scene(
        scene_id="sid-1",
        scene_index=0,
        start_ms=0,
        end_ms=2000,
        duration_ms=2000,
        text="dolor lumbar",
        concept="lower back pain",
        narrative_function="PROBLEM",
    )
    search = SearchResponse(results=[], is_gap=True)
    gap = await gap_handler.enrich_gap(
        s,
        search,
        None,
        product_category="salud",
        target_audience="adultos",
    )
    assert gap is not None
    assert gap.scene_id == s.scene_id
    assert gap.tiktok_keywords
