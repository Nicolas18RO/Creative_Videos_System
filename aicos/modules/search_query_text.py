"""Construcción del texto de consulta semántica (sin cargar ``Embedder`` / torch)."""

from __future__ import annotations

from aicos.models.schemas import SearchRequest
from aicos.taxonomy.constants import NARRATIVE_EXPANSIONS


def build_semantic_query_text(req: SearchRequest) -> str:
    """Prefija expansión narrativa y enriquecimiento global al ``query``."""
    nf = (req.narrative_function or "PROBLEM").upper()
    expansion = NARRATIVE_EXPANSIONS.get(nf, nf.lower())
    base = f"{expansion} {req.query}".strip()
    gen = (req.global_query_enrichment or "").strip()
    if gen:
        return f"{gen} {base}".strip()[:2000]
    return base
