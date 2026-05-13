"""M2: búsqueda semántica + boosting por taxonomía."""

from __future__ import annotations

import logging

from aicos.config import get_config
from aicos.core.embedder import Embedder
from aicos.core.vector_store import VectorStore
from aicos.models.schemas import Recommendation, SearchRequest, SearchResponse
from aicos.modules.search_query_text import build_semantic_query_text

logger = logging.getLogger(__name__)


def _build_query_text(req: SearchRequest) -> str:
    return build_semantic_query_text(req)


def _meta_str(meta: dict, key: str) -> str | None:
    v = meta.get(key)
    if v is None:
        return None
    s = str(v).strip()
    return s if s else None


def build_ranked_recommendations(
    req: SearchRequest, embedder: Embedder, store: VectorStore
) -> list[Recommendation]:
    """Lista completa ordenada por score (taxonomía + similitud); ``intelligence_boost`` en 0."""
    cfg = get_config().search
    pool = max(req.candidate_pool_size, cfg.candidate_pool_size)
    qtext = _build_query_text(req)
    vector = embedder.embed(qtext)
    ids, sims, metas = store.query(vector, n_results=pool)
    used = set(req.used_clip_ids)
    recs: list[Recommendation] = []

    for rank, (cid, sim, meta) in enumerate(zip(ids, sims, metas, strict=False), start=1):
        if not meta:
            continue
        clip_gender = meta.get("gender") or None
        clip_nf = meta.get("narrative_function") or None
        boost = 0.0
        if req.narrative_function and clip_nf == req.narrative_function.upper():
            boost += cfg.narrative_function_boost
        if req.gender_hint and clip_gender == req.gender_hint.upper():
            boost += cfg.gender_match_boost
        if req.is_hook and clip_nf == "HOOK":
            boost += cfg.hook_category_boost
        if cid in used:
            boost -= cfg.repeat_clip_penalty
        final = max(0.0, min(1.0, float(sim) + boost))
        path_str = meta.get("absolute_path") or ""
        recs.append(
            Recommendation(
                clip_id=cid,
                clip_path=path_str,
                rank=rank,
                similarity_score=float(sim),
                taxonomy_boost=boost,
                intelligence_boost=0.0,
                final_score=final,
                narrative_function=clip_nf,
                gender=clip_gender,
                thumbnail_path=meta.get("thumbnail_path") or None,
                variants_in_subcategory=int(meta.get("variants_in_subcategory") or 0),
                clip_subcategory=(meta.get("subcategory") or None) or None,
                clip_context=(meta.get("context") or None) or None,
                clip_semantic_text=(meta.get("semantic_text") or None) or None,
                cm_source_video_id=_meta_str(meta, "cm_source_video_id"),
                cm_visual_cluster_id=_meta_str(meta, "cm_visual_cluster_id"),
                cm_cluster_explicit=_meta_str(meta, "cm_cluster_explicit"),
                cm_visual_embedding_fp=_meta_str(meta, "cm_visual_embedding_fp"),
                cm_master_reel_id=_meta_str(meta, "cm_master_reel_id"),
                cm_embedding_model=_meta_str(meta, "cm_embedding_model"),
                cm_visual_collection=_meta_str(meta, "cm_visual_collection"),
            )
        )

    recs.sort(key=lambda r: (-r.final_score, r.clip_id))
    return recs


def recommend(req: SearchRequest, embedder: Embedder, store: VectorStore) -> SearchResponse:
    """Ejecuta embedding de la consulta, recupera candidatos y aplica boosts (sin capa de inteligencia)."""
    cfg = get_config().search
    gap_threshold = cfg.gap_threshold
    recs = build_ranked_recommendations(req, embedder, store)
    top = recs[: req.n_results]
    for i, r in enumerate(top, start=1):
        top[i - 1] = r.model_copy(update={"rank": i})
    is_gap = not top or top[0].final_score < gap_threshold
    return SearchResponse(results=top, is_gap=is_gap, query_fingerprint=None)

