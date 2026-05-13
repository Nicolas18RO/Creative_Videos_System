"""Construcción de texto semántico enriquecido para embeddings."""

from __future__ import annotations

import re

from aicos.models.schemas import TaxonomyResult
from aicos.taxonomy.constants import (
    CONTEXT_EXPANSIONS,
    GENDER_SEMANTIC,
    NARRATIVE_EXPANSIONS,
    SUBCATEGORY_EXPANSIONS,
)


def _slug_words(s: str) -> str:
    return re.sub(r"_+", " ", s).lower().strip()


def build_semantic_text(t: TaxonomyResult, original_filename: str) -> str:
    """Construye el texto vectorizable para un clip a partir de la taxonomía parseada.

    Si `is_naming_compliant` es False, se usa el nombre de archivo procesado como fallback.
    """
    if not t.is_naming_compliant:
        base = re.sub(r"\.[^.]+$", "", original_filename)
        return " ".join(_slug_words(base).split())

    parts_out: list[str] = []

    if t.asset_kind == "sound_effect":
        parts_out.append("sound effect audio sfx ambient")
        if t.subcategory:
            parts_out.append(_slug_words(t.subcategory))
        if t.context:
            parts_out.append(_slug_words(t.context))
        return " | ".join(parts_out) if len(parts_out) > 1 else parts_out[0]

    if t.gender and t.gender in GENDER_SEMANTIC:
        parts_out.append(GENDER_SEMANTIC[t.gender])

    if t.narrative_function:
        parts_out.append(
            NARRATIVE_EXPANSIONS.get(t.narrative_function, _slug_words(t.narrative_function))
        )

    if t.subcategory:
        sub_exp = SUBCATEGORY_EXPANSIONS.get(
            t.subcategory, _slug_words(t.subcategory) + " " + t.subcategory.lower().replace("_", " ")
        )
        parts_out.append(sub_exp)

    if t.context:
        ctx_key = t.context.upper()
        ctx_exp = CONTEXT_EXPANSIONS.get(ctx_key, _slug_words(t.context))
        parts_out.append(ctx_exp)

    if t.is_ai_generated:
        parts_out.append("ai generated synthetic cgi")

    tail = _slug_words(re.sub(r"\.[^.]+$", "", original_filename))
    parts_out.append(tail)

    return " | ".join(parts_out)
