"""M3: detección de gaps y generación de keywords / prompts (local, sin LLM)."""

from __future__ import annotations

import logging
from typing import Literal

from aicos.core.local_ai.gap_local import (
    generate_image_prompt_local,
    generate_motion_prompt_local,
    generate_tiktok_keywords_local,
)
from aicos.models.schemas import Gap, Scene, SearchResponse

logger = logging.getLogger(__name__)

GapType = Literal["tiktok_search", "ai_generation", "both"]


def classify_gap_type(scene: Scene) -> GapType:
    """Clasifica el tipo de recuperación según concepto y función narrativa."""
    concept_lower = (scene.concept or "").lower()
    medical_inds = (
        "animation",
        "3d",
        "cell",
        "neuron",
        "blood",
        "organ",
        "spine",
        "nerve",
        "intestine",
        "brain",
        "microscopic",
        "laboratory",
        "molecular",
    )
    if any(ind in concept_lower for ind in medical_inds):
        return "ai_generation"
    if (scene.narrative_function or "").upper() == "AUTHORITY":
        return "both"
    return "tiktok_search"


def suggest_taxonomy_placement(scene: Scene) -> str:
    """Sugiere carpeta destino para un clip que cubra la escena."""
    gender = (scene.gender_hint or "N").upper()
    function = (scene.narrative_function or "PROBLEM").upper()
    sub = (scene.concept or "GENERIC").upper().replace(" ", "_")
    return f"{gender}/{function}/{sub}/"


async def enrich_gap(
    scene: Scene,
    search: SearchResponse,
    llm: object | None,
    *,
    product_category: str,
    target_audience: str,
) -> Gap | None:
    """Si la búsqueda indica gap, genera keywords y prompts con plantillas locales."""
    del llm  # API estable; pipeline sin nube.
    if not search.is_gap:
        return None
    gtype = classify_gap_type(scene)
    concept = scene.concept or scene.text[:120]
    nf = scene.narrative_function or "PROBLEM"

    keywords = generate_tiktok_keywords_local(
        scene,
        product_category=product_category,
        target_audience=target_audience,
    )
    img: str | None = None
    motion: str | None = None
    if gtype in ("ai_generation", "both"):
        img = generate_image_prompt_local(scene, product_category=product_category)
        motion = generate_motion_prompt_local(scene)

    return Gap(
        scene_id=scene.scene_id,
        concept=concept,
        narrative_function=nf,
        gap_type=gtype,
        tiktok_keywords=keywords,
        ai_image_prompt=img,
        ai_motion_prompt=motion,
        taxonomy_suggestion=suggest_taxonomy_placement(scene),
    )
