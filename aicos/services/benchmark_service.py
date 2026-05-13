"""Evaluación Fase 3 PRD: baseline vs ranking con inteligencia (sin re-entrenar modelos)."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from aicos.core.embedder import Embedder
from aicos.core.vector_store import VectorStore
from aicos.database.db import RecommendationRow, SceneRow
from aicos.models.schemas import Phase3BenchmarkResponse, SearchRequest
from aicos.modules.clip_recommender import recommend
from aicos.services.search_service import run_search

logger = logging.getLogger(__name__)


def _rank_in_results(truth_clip_id: str, results: list[Any]) -> int | None:
    for i, r in enumerate(results, start=1):
        if r.clip_id == truth_clip_id:
            return i
    return None


def run_phase3_benchmark(
    session: Session,
    embedder: Embedder,
    store: VectorStore,
    *,
    k: int = 5,
    max_cases: int = 80,
) -> Phase3BenchmarkResponse:
    """Compara recuperación sin vs con inteligencia usando feedback positivo rank1 como proxy de verdad."""
    stmt = (
        select(SceneRow.id, SceneRow.concept, SceneRow.narrative_function, RecommendationRow.clip_id)
        .join(RecommendationRow, RecommendationRow.scene_id == SceneRow.id)
        .where(RecommendationRow.rank == 1, RecommendationRow.accepted.is_(True))
        .order_by(SceneRow.id.asc())
        .limit(max_cases)
    )
    rows = list(session.execute(stmt).all())
    trace: list[str] = []
    if not rows:
        return Phase3BenchmarkResponse(
            k=k,
            cases_evaluated=0,
            baseline_precision_at_k=0.0,
            enhanced_precision_at_k=0.0,
            relative_improvement_percent=0.0,
            mean_reciprocal_rank_baseline=0.0,
            mean_reciprocal_rank_enhanced=0.0,
            prd_milestone_hit_rate_enhanced=False,
            prd_milestone_note="Sin escenas con feedback aceptado en rank 1; ejecuta proyectos y feedback para poblar el benchmark.",
            trace=["No hay casos evaluables en SQLite."],
        )

    base_hits = 0
    enh_hits = 0
    mrr_b = 0.0
    mrr_e = 0.0
    used = 0
    for scene_id, concept, nf, truth in rows:
        q = (concept or "").strip()
        if len(q) < 3:
            continue
        req = SearchRequest(
            query=q[:480],
            narrative_function=nf,
            n_results=k,
            candidate_pool_size=max(24, k * 3),
            record_usage=False,
            apply_intelligence=False,
        )
        try:
            b_resp = recommend(req, embedder, store)
            e_req = req.model_copy(update={"apply_intelligence": True})
            e_resp = run_search(session, e_req, embedder, store)
        except Exception as e:
            logger.warning("Benchmark omitió escena %s: %s", scene_id, e)
            continue
        used += 1
        rb = _rank_in_results(str(truth), b_resp.results)
        re_ = _rank_in_results(str(truth), e_resp.results)
        if rb is not None and rb <= k:
            base_hits += 1
            mrr_b += 1.0 / rb
        if re_ is not None and re_ <= k:
            enh_hits += 1
            mrr_e += 1.0 / re_
        if len(trace) < 6:
            trace.append(
                f"scene={str(scene_id)[:8]} truth={str(truth)[:8]} base_rank={rb} enh_rank={re_}"
            )

    if used == 0:
        return Phase3BenchmarkResponse(
            k=k,
            cases_evaluated=0,
            baseline_precision_at_k=0.0,
            enhanced_precision_at_k=0.0,
            relative_improvement_percent=0.0,
            mean_reciprocal_rank_baseline=0.0,
            mean_reciprocal_rank_enhanced=0.0,
            prd_milestone_hit_rate_enhanced=False,
            prd_milestone_note="No se pudo evaluar ninguna escena (errores de búsqueda o conceptos vacíos).",
            trace=trace,
        )

    p_base = base_hits / used
    p_enh = enh_hits / used
    rel = ((p_enh - p_base) / max(p_base, 1e-6)) * 100.0
    mrr_b /= used
    mrr_e /= used
    milestone = p_enh >= 0.75
    note = (
        f"Evaluadas {used} escenas con aceptación rank1. precision@{{k={k}}}: "
        f"baseline={p_base:.3f}, enhanced={p_enh:.3f}. "
        "El milestone PRD (>75% acierto vs baseline) se interpreta aquí como precision@k mejorada "
        "y/o tasa enhanced ≥ 0.75 sobre este proxy de verdad operacional."
    )
    return Phase3BenchmarkResponse(
        k=k,
        cases_evaluated=used,
        baseline_precision_at_k=round(p_base, 4),
        enhanced_precision_at_k=round(p_enh, 4),
        relative_improvement_percent=round(rel, 2),
        mean_reciprocal_rank_baseline=round(mrr_b, 4),
        mean_reciprocal_rank_enhanced=round(mrr_e, 4),
        prd_milestone_hit_rate_enhanced=milestone,
        prd_milestone_note=note,
        trace=trace,
    )
