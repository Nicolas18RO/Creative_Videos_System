"""Parseo de filenames de la biblioteca a los 5 ejes de taxonomía."""

from __future__ import annotations

import re
from pathlib import Path

from aicos.models.schemas import TaxonomyResult
from aicos.taxonomy.constants import KNOWN_SUBCATEGORIES, LEGACY_GENDER_PREFIXES, NARRATIVE_FUNCTIONS


def _normalize_gender(token: str) -> str | None:
    t = token.upper()
    if t in LEGACY_GENDER_PREFIXES:
        t = LEGACY_GENDER_PREFIXES[t]
    if t in {"F", "M", "N", "MIX", "KIDS"}:
        return t
    return None


def _parse_variant(parts: list[str]) -> tuple[int | None, bool, int]:
    """Retorna (variant, is_ai, index_end_exclusive) donde index_end_exclusive corta cola IA+variant."""
    if not parts:
        return None, False, 0
    last = parts[-1]
    m = re.fullmatch(r"(\d{1,3})", last)
    if not m:
        return None, False, len(parts)
    variant = int(m.group(1))
    is_ai = False
    end = len(parts) - 1
    if len(parts) >= 2 and parts[-2].upper() == "IA":
        is_ai = True
        end = len(parts) - 2
    return variant, is_ai, end


def _split_subcategory_context(middle: list[str]) -> tuple[str, str | None]:
    if not middle:
        return "", None
    if len(middle) == 1:
        return middle[0], None
    joined_all = "_".join(middle)
    for k in range(len(middle), 0, -1):
        cand = "_".join(middle[:k])
        if cand in KNOWN_SUBCATEGORIES:
            rest = middle[k:]
            ctx = "_".join(rest) if rest else None
            return cand, ctx
    if len(middle) >= 2:
        return "_".join(middle[:-1]), middle[-1]
    return joined_all, None


def _parse_sound_effect(stem: str) -> TaxonomyResult | None:
    parts = stem.upper().split("_")
    if not parts or parts[0] != "SE":
        return None
    raw = stem.split("_")
    var, _, end_idx = _parse_variant(parts)
    if var is None:
        return TaxonomyResult(
            gender=None,
            narrative_function=None,
            subcategory="_".join(parts[1:]) if len(parts) > 1 else None,
            context=None,
            variant_number=None,
            is_ai_generated=False,
            is_naming_compliant=False,
            raw_parts=raw,
            asset_kind="sound_effect",
        )
    middle = parts[1:end_idx]
    sub, ctx = _split_subcategory_context(middle)
    return TaxonomyResult(
        gender=None,
        narrative_function=None,
        subcategory=sub or None,
        context=ctx,
        variant_number=var,
        is_ai_generated=False,
        is_naming_compliant=True,
        raw_parts=raw,
        asset_kind="sound_effect",
    )


def parse_filename(path_or_name: str | Path) -> TaxonomyResult:
    """Parsea un path o nombre de archivo a :class:`TaxonomyResult`.

    Args:
        path_or_name: Ruta absoluta/relativa o solo el nombre del archivo.

    Returns:
        TaxonomyResult con `is_naming_compliant` según convención documentada.
    """
    p = Path(path_or_name)
    name = p.name
    stem, suffix = p.stem, p.suffix.lower()
    raw = stem.split("_") if stem else []

    if suffix == ".aac" and stem.upper().startswith("SE_"):
        se = _parse_sound_effect(stem)
        if se:
            return se

    parts = [x for x in stem.split("_") if x != ""]
    if len(parts) < 3:
        return TaxonomyResult(
            is_naming_compliant=False,
            raw_parts=raw,
            asset_kind="video",
        )

    gender = _normalize_gender(parts[0])
    if gender is None:
        return TaxonomyResult(is_naming_compliant=False, raw_parts=raw, asset_kind="video")

    if parts[1].upper() not in NARRATIVE_FUNCTIONS:
        return TaxonomyResult(is_naming_compliant=False, raw_parts=raw, asset_kind="video")

    narrative_function = parts[1].upper()
    variant, is_ai, end_idx = _parse_variant(parts)
    if variant is None:
        return TaxonomyResult(is_naming_compliant=False, raw_parts=raw, asset_kind="video")

    middle = parts[2:end_idx]
    if not middle:
        return TaxonomyResult(is_naming_compliant=False, raw_parts=raw, asset_kind="video")

    subcategory, context = _split_subcategory_context([m.upper() for m in middle])
    if not subcategory:
        return TaxonomyResult(is_naming_compliant=False, raw_parts=raw, asset_kind="video")

    compliant = True
    if parts[0].upper() in LEGACY_GENDER_PREFIXES:
        compliant = False
    if re.search(r"[^A-Za-z0-9_.-]", name):
        compliant = False

    return TaxonomyResult(
        gender=gender,
        narrative_function=narrative_function,
        subcategory=subcategory,
        context=context,
        variant_number=variant,
        is_ai_generated=is_ai,
        is_naming_compliant=compliant,
        raw_parts=raw,
        asset_kind="video",
    )
