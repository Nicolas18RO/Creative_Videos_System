"""Extracción de concepto local (determinista, sin APIs de terceros)."""

from __future__ import annotations

import logging

from aicos.core.local_ai.concept_local import extract_concept_local

logger = logging.getLogger(__name__)


async def extract_concept(
    text: str,
    narrative_function: str,
    llm: object | None = None,
    *,
    global_query_enrichment: str | None = None,
) -> str:
    """Obtiene concepto corto alineado a la biblioteca (solo heurísticas locales).

    Args:
        text: Texto de la escena.
        narrative_function: Función narrativa ya inferida.
        llm: Reservado por compatibilidad; no se usa (pipeline local-first).
    """
    if llm is not None:
        logger.debug("extract_concept: parámetro llm ignorado (modo local-first).")
    return extract_concept_local(
        text, narrative_function, global_query_enrichment=global_query_enrichment
    )
