"""Extracción de concepto determinista (regex + heurísticas + spaCy opcional en caché)."""

from __future__ import annotations

import re
import time
from typing import Any

from aicos.taxonomy.constants import DOMAIN_TRANSLATION_MAP

_STOP = frozenset(
    "el la los las un una unos unas y o de del al por para con sin sobre entre "
    "que como cuando si ya muy más menos todo esta este estos es son fue ser "
    "tu su sus nos les me te se lo le da dos uno hay fue sea".split()
)

_CTA_MARKERS = (
    "compra",
    "orden",
    "link",
    "enlace",
    "descuento",
    "oferta",
    "ahora",
    "cta",
    "cupón",
    "cupon",
    "pincha",
    "clic",
    "click",
    "whatsapp",
    "reserva",
    "llama",
    "llama ya",
)

_nlp_cache: Any = None
_nlp_failed: bool = False


def _get_spacy_nlp() -> Any:
    """Carga spaCy una sola vez por proceso (evita ~50 ms de carga por escena)."""
    global _nlp_cache, _nlp_failed
    if _nlp_failed:
        return None
    if _nlp_cache is not None:
        return _nlp_cache
    try:
        import spacy

        _nlp_cache = spacy.load("es_core_news_sm")
    except (ImportError, OSError):
        _nlp_failed = True
        _nlp_cache = None
    return _nlp_cache


def _from_domain_map(text: str) -> str | None:
    tl = text.lower()
    for phrase, en in sorted(DOMAIN_TRANSLATION_MAP.items(), key=lambda x: -len(x[0])):
        if phrase in tl:
            return en
    return None


def _spacy_noun_phrase(text: str) -> str | None:
    nlp = _get_spacy_nlp()
    if nlp is None:
        return None
    doc = nlp(text[:500])
    chunks = [c.text.strip() for c in doc.noun_chunks if len(c.text.strip()) > 2]
    junk = {"esto", "esta", "eso", "nosotros", "ustedes", "personas", "gente", "algo", "nada"}
    chunks = [c for c in chunks if c.lower() not in junk]
    if not chunks:
        return None
    best = max(chunks, key=len)
    return re.sub(r"\s+", " ", best).lower()


def _keyword_tokens(text: str, *, max_tokens: int = 12) -> list[str]:
    raw = re.sub(r"[^\w\sáéíóúñü]", " ", text.lower(), flags=re.UNICODE)
    toks = [t for t in raw.split() if len(t) >= 3 and t not in _STOP]
    return toks[:max_tokens]


def _is_cta_heavy(text: str) -> bool:
    tl = text.lower()
    return any(m in tl for m in _CTA_MARKERS)


def _fallback_concept_from_tokens(tokens: list[str]) -> str:
    if not tokens:
        return "scene context"
    # pseudo-inglés alineado a biblioteca: primeras 5 piezas ASCII simple
    cleaned: list[str] = []
    for t in tokens[:6]:
        t2 = re.sub(r"[^a-z0-9]", "", t)
        if len(t2) >= 3:
            cleaned.append(t2)
    return " ".join(cleaned[:5]) if cleaned else "scene context"


def extract_concept_local(
    text: str,
    narrative_function: str,
    *,
    global_query_enrichment: str | None = None,
) -> str:
    """Concepto corto en inglés/heurístico, <50 ms típico sin carga spaCy inicial."""
    t0 = time.perf_counter()
    t = text.strip()
    glue = (global_query_enrichment or "").strip()
    combined = f"{glue}. {t}".strip() if glue else t
    if not combined:
        return "generic scene"

    dm = _from_domain_map(combined)
    if dm:
        return dm

    sp = _spacy_noun_phrase(combined)
    if sp and len(sp.split()) <= 6:
        mapped = _from_domain_map(sp) or sp
        if mapped:
            return mapped

    toks = _keyword_tokens(combined)
    if _is_cta_heavy(combined):
        base = _fallback_concept_from_tokens(toks)
        if "cta" not in base.lower():
            return (base + " cta call").strip()[:80]

    cleaned = re.sub(r"[^\w\s]", " ", combined.lower())
    out = " ".join(cleaned.split()[:5]) or "scene context"
    elapsed_ms = (time.perf_counter() - t0) * 1000
    if elapsed_ms > 50:
        # solo diagnóstico; no falla
        pass
    return out[:120]
