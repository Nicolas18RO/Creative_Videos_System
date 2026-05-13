"""Clasificación de frames con modelo de visión (M4)."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

from aicos.models.schemas import TaxonomyResult, VisionClassification
from aicos.services.llm_service import LLMService
from aicos.taxonomy.parser import parse_filename

logger = logging.getLogger(__name__)

_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


def _read_prompt(name: str) -> str:
    p = _PROMPTS_DIR / name
    return p.read_text(encoding="utf-8")


def _strip_code_fence(raw: str) -> str:
    s = raw.strip()
    if s.startswith("```"):
        s = re.sub(r"^```\w*\n?", "", s)
        s = re.sub(r"\n?```\s*$", "", s)
    return s.strip()


def parse_vision_json(raw: str) -> VisionClassification:
    """Parsea JSON devuelto por el modelo (tolerante a fences markdown)."""
    data = json.loads(_strip_code_fence(raw))
    return VisionClassification.model_validate(data)


async def classify_frame(image_path: Path, llm: LLMService) -> VisionClassification:
    """Clasifica un frame de video según la taxonomía de la biblioteca."""
    system = _read_prompt("vision_classify.txt")
    raw = await llm.vision_text_response(system, image_path)
    try:
        return parse_vision_json(raw)
    except (json.JSONDecodeError, ValueError) as e:
        logger.error("No se pudo parsear JSON de visión: %s\n%s", e, raw[:500])
        raise


def vision_from_taxonomy(tax: TaxonomyResult, *, filename: str = "") -> VisionClassification:
    """Construye una clasificación estable desde el parser de filenames (sin visión LLM)."""
    g = (tax.gender or "N").strip().upper()
    nf = (tax.narrative_function or "NATURAL").strip().upper()
    sub = (tax.subcategory or "GENERIC_UGC").strip().upper().replace(" ", "_")
    ctx = (tax.context or "").strip() or None
    folder = f"{g}/{nf}/{sub}/"
    if ctx and ctx.upper() not in ("NULL", "NONE", ""):
        folder = f"{g}/{nf}/{sub}/{ctx.upper().replace(' ', '_')}/"
    variant = tax.variant_number or 1
    ia = "_IA" if tax.is_ai_generated else ""
    suggested = f"{g}_{nf}_{sub}{('_' + ctx.upper().replace(' ', '_')) if ctx else ''}{ia}_{variant:02d}.mp4"
    conf = 0.88 if tax.is_naming_compliant else 0.78
    return VisionClassification(
        gender=g,
        narrative_function=nf,
        subcategory=sub,
        context=ctx,
        is_ai_generated=tax.is_ai_generated,
        suggested_filename=suggested[:180],
        suggested_folder=folder[:200],
        confidence=conf,
        tags=["local_filename", tax.asset_kind or "video"],
    )


def classify_from_path_heuristic(video_path: Path) -> VisionClassification:
    """Clasificación local usando solo el nombre de archivo (modo offline / M4)."""
    tax = parse_filename(video_path.name)
    return vision_from_taxonomy(tax, filename=video_path.name)
