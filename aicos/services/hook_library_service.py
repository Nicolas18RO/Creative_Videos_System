"""Hook Library: búsqueda semántica focalizada en clips HOOK (Fase 3 PRD)."""

from __future__ import annotations

import logging
import math

from sqlalchemy import select
from sqlalchemy.orm import Session

from aicos.config import get_config
from aicos.core.embedder import Embedder
from aicos.core.vector_store import VectorStore
from aicos.database.db import ClipRow
from aicos.models.schemas import HookSearchResponse, HookSearchResultItem

logger = logging.getLogger(__name__)


def search_hooks(
    session: Session,
    *,
    query: str,
    embedder: Embedder,
    store: VectorStore,
    n_results: int = 8,
    candidate_pool_size: int = 24,
) -> HookSearchResponse:
    """Recuperación sobre subconjunto HOOK usando Chroma ``where`` + señal ``times_used`` (sin re-embeddings)."""
    cfg_gap = get_config().search.gap_threshold
    vec = embedder.embed(query.strip())
    where = {"narrative_function": "HOOK"}
    try:
        ids, sims, metas = store.query(vec, n_results=candidate_pool_size, where=where)
    except Exception as e:
        logger.warning("Hook search sin filtro where (%s); fallback sin metadata.", e)
        ids, sims, metas = store.query(vec, n_results=candidate_pool_size)

    usage: dict[str, int] = {}
    if ids:
        rows = session.execute(select(ClipRow.id, ClipRow.times_used).where(ClipRow.id.in_(list(ids)))).all()
        usage = {str(i): int(t or 0) for i, t in rows}

    items: list[HookSearchResultItem] = []
    for cid, sim, meta in zip(ids, sims, metas, strict=False):
        if not meta:
            continue
        clip_nf = (meta.get("narrative_function") or "").upper()
        if clip_nf != "HOOK":
            continue
        tu = usage.get(str(cid), 0)
        boost = min(0.05, 0.012 * math.log1p(max(0, tu)))
        fs = max(0.0, min(1.0, float(sim) + boost))
        path_str = str(meta.get("absolute_path") or "")
        items.append(
            HookSearchResultItem(
                clip_id=str(cid),
                clip_path=path_str,
                similarity_score=float(sim),
                final_score=fs,
                narrative_function=clip_nf,
                thumbnail_path=meta.get("thumbnail_path"),
            )
        )
    items.sort(key=lambda x: (-x.final_score, x.clip_id))
    top = items[: max(1, min(int(n_results), 20))]
    is_gap = not top or top[0].final_score < cfg_gap
    return HookSearchResponse(query=query, results=top, is_gap=is_gap)
