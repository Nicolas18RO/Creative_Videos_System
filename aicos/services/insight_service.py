"""Agregados de lectura para la capa de insights (SQLite + conteo Chroma, sin recomputar embeddings)."""

from __future__ import annotations

import logging
import math
import re
import time
from collections import Counter
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import case, func, literal, select
from sqlalchemy.orm import Session

from aicos.config import get_config
from aicos.core.vector_store import VectorStore
from aicos.database.db import ClipRow, GapRow, RecommendationRow, SceneRow, UsageEventRow
from aicos.models.schemas import (
    DatasetCoverageInsights,
    DistributionAnomaly,
    EmbeddingDistributionSummary,
    InsightsGapsResponse,
    InsightsSummaryResponse,
    InsightsTrendsResponse,
    MissingSemanticCluster,
    NFCountPair,
    NarrativeGapPattern,
    SearchFailurePattern,
    SemanticConceptItem,
    TaxonomyBalanceInsights,
    TrendingClusterItem,
    WeakRetrievalZone,
    WeakTaxonomyCluster,
)
from aicos.taxonomy.constants import KNOWN_SUBCATEGORIES, NARRATIVE_FUNCTIONS

logger = logging.getLogger(__name__)

_CACHE: dict[str, tuple[float, Any]] = {}
_DEFAULT_TTL_SEC = 180.0


def _aggregate_audio_signals(session: Session) -> dict[str, Any] | None:
    """Señales ligeras desde ``usage_events`` de análisis de audio (sin embeddings)."""
    cfg = get_config().intelligence
    window = min(90, int(cfg.event_lookback_days))
    cutoff = datetime.utcnow() - timedelta(days=window)
    n_audio = int(
        session.execute(
            select(func.count())
            .select_from(UsageEventRow)
            .where(UsageEventRow.event_type == "audio_segment_search", UsageEventRow.created_at >= cutoff)
        ).scalar_one()
        or 0
    )
    if n_audio == 0:
        return None
    rows = list(
        session.scalars(
            select(UsageEventRow)
            .where(UsageEventRow.event_type == "audio_segment_search", UsageEventRow.created_at >= cutoff)
            .order_by(UsageEventRow.id.asc())
            .limit(800)
        ).all()
    )
    concepts: Counter[str] = Counter()
    nf_hits: Counter[str] = Counter()
    for ev in rows:
        pl = ev.payload if isinstance(ev.payload, dict) else {}
        c = str(pl.get("concept") or "").strip().lower()
        if len(c) >= 4:
            for tok in re.findall(r"[a-záéíóúñ]{4,}", c):
                concepts[tok] += 1
        if ev.narrative_function:
            nf_hits[str(ev.narrative_function).upper()] += 1
    top_concepts = [w for w, _ in concepts.most_common(12)]
    return {
        "audio_segment_searches_in_window": n_audio,
        "lookback_days": window,
        "top_concept_tokens_from_audio": top_concepts,
        "narrative_function_audio_event_counts": dict(nf_hits.most_common(8)),
    }


def invalidate_insights_cache() -> None:
    """Invalida la caché en memoria (p. ej. tras ``?refresh=true``)."""
    _CACHE.clear()


def _cache_get(key: str, ttl: float) -> Any | None:
    hit = _CACHE.get(key)
    if hit is None:
        return None
    age = time.monotonic() - hit[0]
    if age > ttl:
        return None
    return hit[1]


def _cache_set(key: str, value: Any) -> None:
    _CACHE[key] = (time.monotonic(), value)


def _chroma_clip_count(vs: VectorStore | None = None) -> tuple[int | None, VectorStore]:
    """Cuenta vectores indexados sin cargar embeddings."""
    store = vs or VectorStore()
    try:
        return int(store.collection.count()), store
    except Exception as e:
        logger.warning("No se pudo leer conteo Chroma: %s", e)
        return None, store


def _narrative_function_counts(session: Session) -> dict[str, int]:
    rows = session.execute(
        select(ClipRow.narrative_function, func.count())
        .where(ClipRow.narrative_function.is_not(None))
        .group_by(ClipRow.narrative_function)
    ).all()
    out: dict[str, int] = {}
    for nf, c in rows:
        key = (nf or "").strip().upper() or "UNKNOWN"
        out[key] = int(c or 0)
    return out


def _balance_score_from_counts(counts_by_nf: dict[str, int]) -> tuple[float, float]:
    """Devuelve (score 0–100, coeficiente de variación de la distribución en 8 funciones)."""
    counts = [max(0, counts_by_nf.get(nf, 0)) for nf in sorted(NARRATIVE_FUNCTIONS)]
    total = sum(counts)
    if total == 0:
        return 0.0, 0.0
    mean = total / len(counts)
    var = sum((c - mean) ** 2 for c in counts) / len(counts)
    std = math.sqrt(max(0.0, var))
    cv = std / mean if mean > 0 else 0.0
    score = max(0.0, min(100.0, 100.0 * (1.0 - min(cv, 2.0) / 2.0)))
    return score, cv


def _duration_bucket_expr():
    return case(
        (ClipRow.duration_ms.is_(None), literal("unknown")),
        (ClipRow.duration_ms < 2000, literal("lt_2s")),
        (ClipRow.duration_ms < 5000, literal("2s_5s")),
        (ClipRow.duration_ms < 12000, literal("5s_12s")),
        (ClipRow.duration_ms < 30000, literal("12s_30s")),
        else_=literal("ge_30s"),
    )


def _collect_distribution_anomalies(session: Session, total_clips: int) -> list[DistributionAnomaly]:
    if total_clips <= 0:
        return []
    b = _duration_bucket_expr()
    rows = session.execute(select(b, func.count()).group_by(b)).all()
    anomalies: list[DistributionAnomaly] = []
    for bucket, cnt in rows:
        ratio = int(cnt or 0) / total_clips
        key = str(bucket or "unknown")
        if key != "unknown" and ratio >= 0.82:
            anomalies.append(
                DistributionAnomaly(
                    kind="duration_skew",
                    detail=f"{100.0 * ratio:.1f}% de clips en bucket de duración «{key}»",
                    severity="high" if ratio >= 0.92 else "medium",
                )
            )
    gender_rows = session.execute(select(ClipRow.gender, func.count()).group_by(ClipRow.gender)).all()
    g_counts = [(str(g), int(c or 0)) for g, c in gender_rows if g is not None and str(g).strip() != ""]
    g_total = sum(c for _, c in g_counts)
    if g_total > 0:
        for g, c in g_counts:
            ratio = c / g_total
            if ratio >= 0.75:
                anomalies.append(
                    DistributionAnomaly(
                        kind="gender_skew",
                        detail=f"Género «{g}» concentra {100.0 * ratio:.1f}% de clips con género definido",
                        severity="medium",
                    )
                )
    return anomalies[:12]


def _system_health_score(
    *,
    naming_ratio: float,
    sync_ratio: float | None,
    taxonomy_balance: float,
    gap_density_penalty: float,
) -> float:
    sync = sync_ratio if sync_ratio is not None else 0.72
    raw = 0.34 * (100.0 * naming_ratio) + 0.34 * (100.0 * sync) + 0.22 * taxonomy_balance
    raw -= 0.10 * min(100.0, gap_density_penalty * 100.0)
    return max(0.0, min(100.0, raw))


def _weak_nf_clusters(nf_counts: dict[str, int]) -> list[WeakTaxonomyCluster]:
    vals = [max(0, nf_counts.get(nf, 0)) for nf in NARRATIVE_FUNCTIONS]
    if not any(vals):
        return []
    mean = sum(vals) / len(vals)
    std = math.sqrt(sum((v - mean) ** 2 for v in vals) / len(vals)) or 1e-6
    out: list[WeakTaxonomyCluster] = []
    for nf in NARRATIVE_FUNCTIONS:
        c = nf_counts.get(nf, 0)
        z = (c - mean) / std
        if z < -0.85:
            out.append(WeakTaxonomyCluster(narrative_function=nf, clip_count=c, z_score_vs_mean=round(float(z), 3)))
    out.sort(key=lambda x: x.z_score_vs_mean)
    return out[:6]


def build_insights_summary(session: Session, *, refresh: bool = False) -> InsightsSummaryResponse:
    key = "insights_summary"
    if not refresh:
        hit = _cache_get(key, _DEFAULT_TTL_SEC)
        if isinstance(hit, InsightsSummaryResponse):
            return hit
    if refresh:
        _CACHE.pop(key, None)

    stats_total = int(session.execute(select(func.count()).select_from(ClipRow)).scalar_one() or 0)
    compliant = int(
        session.execute(
            select(func.count()).select_from(ClipRow).where(ClipRow.naming_compliant.is_(True))
        ).scalar_one()
        or 0
    )
    naming_ratio = (compliant / stats_total) if stats_total else 0.0

    chroma_n, vs = _chroma_clip_count()
    if chroma_n is not None and stats_total > 0:
        sync_ratio = min(chroma_n, stats_total) / max(chroma_n, stats_total)
    elif stats_total == 0:
        sync_ratio = 1.0
    else:
        sync_ratio = None

    nf_counts = _narrative_function_counts(session)
    balance_score, cv = _balance_score_from_counts(nf_counts)

    sub_rows = session.execute(
        select(ClipRow.subcategory, func.count())
        .where(ClipRow.subcategory.is_not(None), ClipRow.subcategory != "")
        .group_by(ClipRow.subcategory)
    ).all()
    distinct_subs = len(sub_rows)
    sub_map = {((s or "").strip().upper()): int(c or 0) for s, c in sub_rows}
    known = KNOWN_SUBCATEGORIES
    represented = sum(1 for k in known if sub_map.get(k, 0) > 0)
    under_low = sum(1 for k in known if 0 < sub_map.get(k, 0) <= 1)
    catalog = len(known)
    coverage_ratio = represented / catalog if catalog else 0.0

    scene_total = int(session.execute(select(func.count()).select_from(SceneRow)).scalar_one() or 0)
    gap_rows_n = int(session.execute(select(func.count()).select_from(GapRow)).scalar_one() or 0)
    gap_density = (gap_rows_n / scene_total) if scene_total else 0.0

    anomalies = _collect_distribution_anomalies(session, stats_total)

    cfg = get_config()
    emb = cfg.embeddings

    dataset = DatasetCoverageInsights(
        total_clips=stats_total,
        distinct_subcategories=distinct_subs,
        known_subcategory_catalog_size=catalog,
        known_subcategories_represented=represented,
        coverage_ratio_of_known_catalog=round(coverage_ratio, 4),
        underrepresented_known_subcategories_le_1_clip=under_low,
    )
    taxonomy = TaxonomyBalanceInsights(
        narrative_function_counts=nf_counts,
        balance_score=round(balance_score, 2),
        coefficient_of_variation=round(cv, 4),
        weak_taxonomy_clusters=_weak_nf_clusters(nf_counts),
    )
    embed_summary = EmbeddingDistributionSummary(
        sqlite_clip_count=stats_total,
        chroma_indexed_count=chroma_n,
        sync_ratio=None if sync_ratio is None else round(sync_ratio, 4),
        collection_name=vs.collection_name,
        configured_embedding_dimensions=int(emb.dimensions),
    )

    audio_sig = _aggregate_audio_signals(session)

    summary = InsightsSummaryResponse(
        system_health_score=_system_health_score(
            naming_ratio=naming_ratio,
            sync_ratio=sync_ratio,
            taxonomy_balance=balance_score,
            gap_density_penalty=min(1.0, gap_density * 2.0),
        ),
        dataset_coverage=dataset,
        taxonomy_balance=taxonomy,
        embedding_distribution_summary=embed_summary,
        clip_distribution_anomalies=anomalies,
        audio_derived_signals=audio_sig,
    )
    _cache_set(key, summary)
    return summary


def build_insights_gaps(session: Session, *, refresh: bool = False) -> InsightsGapsResponse:
    key = "insights_gaps"
    if not refresh:
        hit = _cache_get(key, _DEFAULT_TTL_SEC)
        if isinstance(hit, InsightsGapsResponse):
            return hit
    if refresh:
        _CACHE.pop(key, None)

    gap_type_rows = session.execute(
        select(GapRow.gap_type, func.count()).group_by(GapRow.gap_type).order_by(func.count().desc())
    ).all()
    patterns: list[NarrativeGapPattern] = []
    for gt, cnt in gap_type_rows[:20]:
        nf_sub = session.execute(
            select(GapRow.narrative_function, func.count())
            .where(GapRow.gap_type == gt)
            .group_by(GapRow.narrative_function)
            .order_by(func.count().desc())
            .limit(5)
        ).all()
        patterns.append(
            NarrativeGapPattern(
                gap_type=str(gt),
                count=int(cnt or 0),
                top_narrative_functions=[
                    NFCountPair(narrative_function=str(nf), count=int(c or 0)) for nf, c in nf_sub
                ],
            )
        )

    sub_rows = session.execute(
        select(ClipRow.subcategory, func.count())
        .where(ClipRow.subcategory.is_not(None), ClipRow.subcategory != "")
        .group_by(ClipRow.subcategory)
    ).all()
    sub_map = {((s or "").strip().upper()): int(c or 0) for s, c in sub_rows}
    missing_clusters: list[MissingSemanticCluster] = []
    for k in sorted(KNOWN_SUBCATEGORIES):
        n = sub_map.get(k, 0)
        if n == 0:
            missing_clusters.append(
                MissingSemanticCluster(cluster_label=k, clip_count=0, note="sin clips en catálogo conocido")
            )
    missing_clusters = missing_clusters[:80]

    low_sim = session.execute(
        select(SceneRow.narrative_function, func.count())
        .join(RecommendationRow, RecommendationRow.scene_id == SceneRow.id)
        .where(RecommendationRow.rank == 1, RecommendationRow.similarity_score < 0.35)
        .group_by(SceneRow.narrative_function)
    ).all()
    weak_zones = [
        WeakRetrievalZone(
            zone_label=f"rank1_sim<0.35 | nf={nf}",
            scene_hits=int(c or 0),
            narrative_function=str(nf),
        )
        for nf, c in sorted(low_sim, key=lambda x: -int(x[1] or 0))[:12]
    ]

    rejected = session.execute(
        select(SceneRow.narrative_function, func.count())
        .join(RecommendationRow, RecommendationRow.scene_id == SceneRow.id)
        .where(RecommendationRow.rank == 1, RecommendationRow.accepted.is_(False))
        .group_by(SceneRow.narrative_function)
    ).all()
    failures = [
        SearchFailurePattern(
            pattern_label="rank1_rechazada",
            narrative_function=str(nf),
            count=int(c or 0),
        )
        for nf, c in sorted(rejected, key=lambda x: -int(x[1] or 0))[:12]
    ]

    out = InsightsGapsResponse(
        narrative_gap_patterns=patterns,
        missing_semantic_clusters=missing_clusters,
        weak_retrieval_zones=weak_zones,
        search_failure_patterns=failures,
    )
    _cache_set(key, out)
    return out


_TOKEN_RE = re.compile(r"[a-zA-ZáéíóúñÁÉÍÓÚÑ]{4,}")


def _top_semantic_terms(
    session: Session, *, sample_limit: int = 400, top_n: int = 24, deterministic: bool = False
) -> list[SemanticConceptItem]:
    base = (
        select(ClipRow.semantic_text)
        .where(ClipRow.semantic_text.is_not(None), ClipRow.semantic_text != "")
    )
    stmt = base.order_by(ClipRow.id.asc()).limit(sample_limit) if deterministic else base.order_by(func.random()).limit(sample_limit)
    texts = [str(t or "") for (t,) in session.execute(stmt).all()]
    stop = {
        "this",
        "that",
        "with",
        "from",
        "para",
        "como",
        "cada",
        "sobre",
        "entre",
        "clip",
        "video",
        "woman",
        "female",
        "male",
        "man",
        "person",
    }
    ctr: Counter[str] = Counter()
    for tx in texts:
        for w in _TOKEN_RE.findall(tx.lower()):
            if w in stop:
                continue
            ctr[w] += 1
    return [SemanticConceptItem(term=w, count=c) for w, c in ctr.most_common(top_n)]


def build_insights_trends(
    session: Session, *, refresh: bool = False, deterministic: bool = False
) -> InsightsTrendsResponse:
    """Si ``deterministic`` es True, el muestreo de texto semántico es estable (``ORDER BY id``), p. ej. para el motor de decisiones."""
    key = "insights_trends_det" if deterministic else "insights_trends"
    if not refresh:
        hit = _cache_get(key, _DEFAULT_TTL_SEC)
        if isinstance(hit, InsightsTrendsResponse):
            return hit
    if refresh:
        _CACHE.pop(key, None)

    top_sub = session.execute(
        select(ClipRow.subcategory, func.count())
        .where(ClipRow.subcategory.is_not(None), ClipRow.subcategory != "")
        .group_by(ClipRow.subcategory)
        .order_by(func.count().desc())
        .limit(25)
    ).all()
    trending_clusters = [
        TrendingClusterItem(cluster_id=str(sub or "—"), clip_count=int(c or 0), subcategory=str(sub or ""))
        for sub, c in top_sub
    ]

    nf_counts = _narrative_function_counts(session)
    dominant = max(nf_counts.items(), key=lambda kv: kv[1])[0] if nf_counts else "—"

    concepts = _top_semantic_terms(session, deterministic=deterministic)

    out = InsightsTrendsResponse(
        most_frequent_semantic_concepts=concepts,
        trending_clusters=trending_clusters,
        narrative_function_distribution=nf_counts,
        dominant_narrative_pattern=f"{dominant}-heavy" if dominant != "—" else "vacío",
    )
    _cache_set(key, out)
    return out
