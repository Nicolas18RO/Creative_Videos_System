"""Enriquecimiento de consulta semántica con contexto global."""

from __future__ import annotations

from aicos.domain.context.entities import GlobalContext


def build_global_query_enrichment(ctx: GlobalContext | None) -> str | None:
    """Texto compacto para prefijar embeddings de búsqueda (clip selection)."""
    if ctx is None:
        return None
    parts = [
        ctx.topic,
        ctx.industry.value,
        ctx.dominant_emotion,
        ctx.narrative_arc.value,
        ctx.visual_style.value,
        " ".join(ctx.semantic_anchors[:16]),
    ]
    line = " ".join(p for p in parts if p).strip()
    return line[:480] if line else None
