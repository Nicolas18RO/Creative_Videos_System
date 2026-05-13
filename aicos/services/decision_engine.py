"""Motor de decisiones explicables (Fase 4): interpreta insights + metadatos SQLite, sin ML ni re-embeddings."""

from __future__ import annotations

import time
from typing import Literal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from aicos.database.db import ClipRow
from aicos.models.schemas import (
    CategoryIntervention,
    ClusterInstability,
    DecisionsImpactResponse,
    DecisionsListResponse,
    DecisionsSummaryResponse,
    ImpactedArea,
    InsightsGapsResponse,
    InsightsSummaryResponse,
    InsightsTrendsResponse,
    SystemDecision,
)
from aicos.services.insight_service import (
    build_insights_gaps,
    build_insights_summary,
    build_insights_trends,
)

_DECISION_CACHE: tuple[float, list[SystemDecision]] | None = None
_TTL_SEC = 300.0
_MAX_DECISIONS = 120


def invalidate_decisions_cache() -> None:
    """Vacía la caché de decisiones (p. ej. ``?refresh=true`` en la API)."""
    global _DECISION_CACHE
    _DECISION_CACHE = None


def _cache_get() -> list[SystemDecision] | None:
    if _DECISION_CACHE is None:
        return None
    age = time.monotonic() - _DECISION_CACHE[0]
    if age > _TTL_SEC:
        return None
    return _DECISION_CACHE[1]


def _cache_set(decisions: list[SystemDecision]) -> None:
    global _DECISION_CACHE
    _DECISION_CACHE = (time.monotonic(), decisions)


def _sev_rank(s: Literal["low", "medium", "high"]) -> int:
    return {"high": 0, "medium": 1, "low": 2}[s]


def _max_sev(a: Literal["low", "medium", "high"], b: Literal["low", "medium", "high"]) -> Literal["low", "medium", "high"]:
    return a if _sev_rank(a) <= _sev_rank(b) else b


def _materialize_decisions(session: Session) -> list[SystemDecision]:
    """Genera la lista completa de decisiones (orden estable por severidad, tipo, id)."""
    summary = build_insights_summary(session, refresh=False)
    gaps = build_insights_gaps(session, refresh=False)
    trends = build_insights_trends(session, refresh=False, deterministic=True)
    raw: list[SystemDecision] = []
    raw.extend(_decisions_from_insights_summary(summary))
    raw.extend(_decisions_from_insights_gaps(gaps))
    raw.extend(_decisions_from_insights_trends(trends, summary))
    raw.extend(_decisions_from_sql_clip_signals(session, summary))
    raw.sort(key=lambda d: (_sev_rank(d.severity), d.type, d.id))
    trimmed = raw[:_MAX_DECISIONS]
    return [d.model_copy(update={"id": f"DEC-{i:04d}"}) for i, d in enumerate(trimmed, start=1)]


def _stable_decision_id(prefix: str, key: str) -> str:
    """Id estable antes del re-numerado global (clave determinista)."""
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in key)[:80]
    return f"{prefix}-{safe}"


def _decisions_from_insights_summary(s: InsightsSummaryResponse) -> list[SystemDecision]:
    out: list[SystemDecision] = []
    health = float(s.system_health_score)
    if health < 40.0:
        out.append(
            SystemDecision(
                id=_stable_decision_id("pre", "health-low"),
                type="optimization",
                severity="high",
                affected_entities=["system:health"],
                explanation=(
                    f"Puntuación de salud del sistema baja ({health:.1f}/100): naming, sincronía índice/SQLite, "
                    "balance taxonómico o densidad de gaps penalizan el estado global."
                ),
                suggested_action="Revisar cumplimiento de nombres, ejecutar validación Chroma/SQLite y equilibrar funciones narrativas antes de nuevos proyectos.",
                confidence_score=0.88,
            )
        )
    elif health < 68.0:
        out.append(
            SystemDecision(
                id=_stable_decision_id("pre", "health-medium"),
                type="optimization",
                severity="medium",
                affected_entities=["system:health"],
                explanation=f"Salud del sistema moderada ({health:.1f}/100); conviene priorizar mejoras incrementales.",
                suggested_action="Abrir pestaña Insights, usar «Recompute» y atacar primero anomalías de distribución y cobertura.",
                confidence_score=0.72,
            )
        )

    emb = s.embedding_distribution_summary
    sr = emb.sync_ratio
    if sr is not None and sr < 0.92:
        sev: Literal["low", "medium", "high"] = "high" if sr < 0.85 else "medium"
        out.append(
            SystemDecision(
                id=_stable_decision_id("pre", f"sync-{sr:.3f}"),
                type="optimization",
                severity=sev,
                affected_entities=["vector_index:chroma", f"collection:{emb.collection_name}"],
                explanation=(
                    f"Desalineación entre SQLite ({emb.sqlite_clip_count} clips) y Chroma ({emb.chroma_indexed_count}): "
                    f"sync_ratio={sr:.3f}. Suele indicar clips sin reindexar o colección obsoleta."
                ),
                suggested_action="Ejecutar bootstrap/reindexación incremental de la colección de clips (sin cambiar modelo de embedding) hasta alinear conteos.",
                confidence_score=0.91 if sr < 0.85 else 0.78,
            )
        )

    dc = s.dataset_coverage
    if dc.coverage_ratio_of_known_catalog < 0.22:
        out.append(
            SystemDecision(
                id=_stable_decision_id("pre", "coverage-low"),
                type="content",
                severity="high",
                affected_entities=["taxonomy:known_subcategories"],
                explanation=(
                    f"Cobertura baja del catálogo conocido: {100.0 * dc.coverage_ratio_of_known_catalog:.1f}% "
                    f"({dc.known_subcategories_represented}/{dc.known_subcategory_catalog_size} subcategorías con clips)."
                ),
                suggested_action="Planificar captura o reclasificación de clips para subcategorías vacías priorizadas por negocio.",
                confidence_score=0.84,
            )
        )
    elif dc.underrepresented_known_subcategories_le_1_clip >= 35:
        out.append(
            SystemDecision(
                id=_stable_decision_id("pre", "underrep-many"),
                type="content",
                severity="medium",
                affected_entities=["taxonomy:known_subcategories"],
                explanation=(
                    f"Muchas subcategorías del catálogo con ≤1 clip ({dc.underrepresented_known_subcategories_le_1_clip}); "
                    "riesgo de huecos al armar creativos."
                ),
                suggested_action="Agrupar subcategorías similares o añadir variantes en las ramas más usadas en guiones reales.",
                confidence_score=0.7,
            )
        )

    for w in s.taxonomy_balance.weak_taxonomy_clusters[:8]:
        out.append(
            SystemDecision(
                id=_stable_decision_id("nf", w.narrative_function),
                type="optimization",
                severity="medium",
                affected_entities=[f"narrative_function:{w.narrative_function}"],
                explanation=(
                    f"Función narrativa «{w.narrative_function}» con pocos clips (z={w.z_score_vs_mean}) frente a la media; "
                    "clusters taxonómicos débiles para esa función."
                ),
                suggested_action=f"Aumentar biblioteca o reclasificar clips hacia «{w.narrative_function}» si los guiones lo requieren.",
                confidence_score=0.68,
            )
        )

    for an in s.clip_distribution_anomalies:
        sev = an.severity if an.severity in ("low", "medium", "high") else "medium"
        out.append(
            SystemDecision(
                id=_stable_decision_id("anom", an.kind + an.detail[:40]),
                type="optimization",
                severity=sev,
                affected_entities=[f"anomaly:{an.kind}"],
                explanation=an.detail,
                suggested_action="Revisar ingestión de duraciones o género; evitar sesgos que degraden búsqueda por metadatos.",
                confidence_score=0.62 if sev == "low" else 0.75,
            )
        )

    nf_counts = s.taxonomy_balance.narrative_function_counts
    total_nf = sum(max(0, v) for v in nf_counts.values())
    if total_nf > 50:
        top_nf, top_c = max(nf_counts.items(), key=lambda kv: kv[1])
        ratio = top_c / total_nf
        if ratio > 0.52:
            out.append(
                SystemDecision(
                    id=_stable_decision_id("skew", top_nf),
                    type="optimization",
                    severity="medium",
                    affected_entities=[f"narrative_function:{top_nf}"],
                    explanation=(
                        f"Distribución muy sesgada: «{top_nf}» representa ~{100.0 * ratio:.0f}% de clips con función conocida; "
                        "dominancia que puede empobrecer recuperación en otras partes del arco narrativo."
                    ),
                    suggested_action="Complementar biblioteca con otras funciones narrativas o revisar clasificación automática.",
                    confidence_score=0.66,
                )
            )

    ads = s.audio_derived_signals
    if isinstance(ads, dict):
        n = int(ads.get("audio_segment_searches_in_window") or 0)
        if n >= 15:
            out.append(
                SystemDecision(
                    id=_stable_decision_id("audio", "volume"),
                    type="retrieval",
                    severity="low",
                    affected_entities=["audio:voice_over_queries"],
                    explanation=(
                        f"Memoria de análisis de audio: {n} búsquedas por segmento en la ventana configurada; "
                        "el voice-over está acoplado al sistema de ranking."
                    ),
                    suggested_action=(
                        "Contrastar top_concept_tokens_from_audio en /insights/summary con cobertura de biblioteca."
                    ),
                    confidence_score=0.6,
                )
            )

    return out


def _decisions_from_insights_gaps(g: InsightsGapsResponse) -> list[SystemDecision]:
    out: list[SystemDecision] = []
    for p in g.narrative_gap_patterns[:8]:
        if p.count < 3:
            continue
        sev: Literal["low", "medium", "high"] = "high" if p.count >= 25 else "medium"
        top = ", ".join(f"{x.narrative_function}:{x.count}" for x in p.top_narrative_functions[:3])
        out.append(
            SystemDecision(
                id=_stable_decision_id("gaptype", p.gap_type),
                type="content",
                severity=sev,
                affected_entities=[f"gap_type:{p.gap_type}"],
                explanation=f"Patrón de gaps M3 frecuente ({p.count} casos). Top funciones narrativas: {top or '—'}.",
                suggested_action="Enriquecer taxonomía o clips alineados a este tipo de gap en los guiones donde aparece.",
                confidence_score=0.74 if sev == "high" else 0.61,
            )
        )

    missing = [m for m in g.missing_semantic_clusters if m.clip_count == 0]
    if len(missing) >= 8:
        sample = [f"category:{m.cluster_label}" for m in missing[:20]]
        out.append(
            SystemDecision(
                id=_stable_decision_id("miss", str(len(missing))),
                type="content",
                severity="high" if len(missing) >= 40 else "medium",
                affected_entities=sample,
                explanation=(
                    f"Hay {len(missing)} subcategorías del catálogo conocido sin ningún clip; huecos semánticos estructurales."
                ),
                suggested_action="Priorizar producción o importación de clips para las subcategorías vacías más usadas en producto.",
                confidence_score=0.82 if len(missing) >= 40 else 0.7,
            )
        )

    for z in g.weak_retrieval_zones:
        if z.scene_hits < 4:
            continue
        sev: Literal["low", "medium", "high"] = "high" if z.scene_hits >= 14 else "medium"
        out.append(
            SystemDecision(
                id=_stable_decision_id("weakret", z.narrative_function),
                type="retrieval",
                severity=sev,
                affected_entities=[f"narrative_function:{z.narrative_function}", z.zone_label],
                explanation=(
                    f"Zona de recuperación débil: {z.scene_hits} escenas con recomendación #1 de baja similitud "
                    f"(<{0.35}) en función «{z.narrative_function}»."
                ),
                suggested_action="Ajustar umbrales de búsqueda, revisar expansiones semánticas de esa función o añadir clips de mayor similitud típica.",
                confidence_score=0.79 if sev == "high" else 0.65,
            )
        )

    for f in g.search_failure_patterns:
        if f.count < 4:
            continue
        sev: Literal["low", "medium", "high"] = "medium" if f.count < 15 else "high"
        out.append(
            SystemDecision(
                id=_stable_decision_id("reject", f.narrative_function),
                type="retrieval",
                severity=sev,
                affected_entities=[f"narrative_function:{f.narrative_function}", f"pattern:{f.pattern_label}"],
                explanation=(
                    f"Patrón de fallo en búsqueda: {f.count} veces rank1 marcada como rechazada en «{f.narrative_function}»."
                ),
                suggested_action="Analizar feedback de esas escenas; considerar penalizar clips rechazados repetidamente o mejorar texto semántico.",
                confidence_score=0.71,
            )
        )
    return out


def _decisions_from_insights_trends(
    t: InsightsTrendsResponse, summary: InsightsSummaryResponse
) -> list[SystemDecision]:
    out: list[SystemDecision] = []
    for c in t.trending_clusters[:5]:
        if c.clip_count < 2:
            continue
        ratio = c.clip_count / max(1, summary.dataset_coverage.total_clips)
        if ratio > 0.18:
            out.append(
                SystemDecision(
                    id=_stable_decision_id("dupheavy", c.subcategory or c.cluster_id),
                    type="optimization",
                    severity="medium",
                    affected_entities=[f"subcategory:{c.subcategory}"],
                    explanation=(
                        f"Subcategoría «{c.subcategory}» con {c.clip_count} clips (~{100.0 * ratio:.0f}% del total): "
                        "posible cluster duplicado o redundante."
                    ),
                    suggested_action="Deduplicar variantes semánticas o fusionar contextos; revisar nombres de archivo y variant_number.",
                    confidence_score=0.63,
                )
            )
    return out


def _decisions_from_sql_clip_signals(session: Session, summary: InsightsSummaryResponse) -> list[SystemDecision]:
    out: list[SystemDecision] = []
    total = max(1, summary.dataset_coverage.total_clips)

    n_reclass = int(
        session.execute(
            select(func.count()).select_from(ClipRow).where(ClipRow.needs_reclassification.is_(True))
        ).scalar_one()
        or 0
    )
    if n_reclass > 0:
        rows = list(
            session.scalars(
                select(ClipRow.id).where(ClipRow.needs_reclassification.is_(True)).order_by(ClipRow.id.asc()).limit(25)
            ).all()
        )
        sev: Literal["low", "medium", "high"] = "high" if (n_reclass / total) > 0.08 else "medium"
        out.append(
            SystemDecision(
                id=_stable_decision_id("reclass", str(n_reclass)),
                type="content",
                severity=sev,
                affected_entities=[f"clip:{i}" for i in rows],
                explanation=f"{n_reclass} clips marcados como needs_reclassification; degradan consistencia del índice.",
                suggested_action="Pasar lote por M4/visión o revisión manual según `needs_reclassification` y reindexar metadatos.",
                confidence_score=0.86 if sev == "high" else 0.74,
            )
        )

    n_bad_name = int(
        session.execute(
            select(func.count()).select_from(ClipRow).where(ClipRow.naming_compliant.is_(False))
        ).scalar_one()
        or 0
    )
    if n_bad_name > 0:
        sev = "high" if (n_bad_name / total) > 0.12 else "medium"
        out.append(
            SystemDecision(
                id=_stable_decision_id("naming", str(n_bad_name)),
                type="content",
                severity=sev,
                affected_entities=["library:naming"],
                explanation=f"{n_bad_name} clips con naming_compliant=false; el parser y el embedding semántico sufren.",
                suggested_action="Corregir nombres según convención o mover a incoming para auto-organizer.",
                confidence_score=0.8,
            )
        )

    dup_rows = session.execute(
        select(ClipRow.file_hash, func.count())
        .where(ClipRow.file_hash.is_not(None), ClipRow.file_hash != "")
        .group_by(ClipRow.file_hash)
        .having(func.count() > 1)
        .order_by(func.count().desc())
        .limit(12)
    ).all()
    for h, cnt in dup_rows:
        if int(cnt or 0) < 2:
            continue
        hid = str(h)[:16]
        out.append(
            SystemDecision(
                id=_stable_decision_id("duphash", hid),
                type="optimization",
                severity="medium",
                affected_entities=[f"file_hash:{hid}"],
                explanation=f"file_hash repetido ({cnt} clips): posible duplicado físico o copias en biblioteca.",
                suggested_action="Consolidar clips duplicados o distinguir rutas absolutas si son assets distintos.",
                confidence_score=0.7,
            )
        )

    iso_rows = list(
        session.scalars(
            select(ClipRow.id)
            .where(
                ClipRow.semantic_text.is_not(None),
                func.length(func.trim(ClipRow.semantic_text)) < 48,
            )
            .order_by(ClipRow.id.asc())
            .limit(30)
        ).all()
    )
    if iso_rows:
        out.append(
            SystemDecision(
                id=_stable_decision_id("isolated", str(len(iso_rows))),
                type="content",
                severity="low",
                affected_entities=[f"clip:{i}" for i in iso_rows],
                explanation=(
                    f"Al menos {len(iso_rows)} clips con texto semántico muy corto (<48 caracteres); aislados en recuperación vectorial."
                ),
                suggested_action="Regenerar o ampliar semantic_text desde transcript/taxonomía antes de reindexar texto.",
                confidence_score=0.58,
            )
        )

    return out


def get_decisions(session: Session, *, refresh: bool) -> list[SystemDecision]:
    if refresh:
        invalidate_decisions_cache()
    else:
        hit = _cache_get()
        if hit is not None:
            return hit
    decisions = _materialize_decisions(session)
    _cache_set(decisions)
    return decisions


def build_decisions_summary(session: Session, *, refresh: bool = False) -> DecisionsSummaryResponse:
    decisions = get_decisions(session, refresh=refresh)
    high = sum(1 for d in decisions if d.severity == "high")
    dist: dict[str, int] = {}
    for d in decisions:
        dist[d.type] = dist.get(d.type, 0) + 1
    penalty = high * 18.0 + sum(1 for d in decisions if d.severity == "medium") * 8.0 + sum(
        1 for d in decisions if d.severity == "low"
    ) * 2.5
    score = max(0.0, min(100.0, 100.0 - min(penalty, 95.0)))
    return DecisionsSummaryResponse(
        system_decision_score=round(score, 2),
        total_active_decisions=len(decisions),
        high_severity_count=high,
        decision_distribution=dist,
    )


def build_decisions_list(
    session: Session,
    *,
    refresh: bool = False,
    limit: int = 50,
    offset: int = 0,
    decision_type: str | None = None,
    severity: str | None = None,
) -> DecisionsListResponse:
    decisions = get_decisions(session, refresh=refresh)
    filtered = decisions
    if decision_type in ("optimization", "content", "retrieval"):
        filtered = [d for d in filtered if d.type == decision_type]
    if severity in ("low", "medium", "high"):
        filtered = [d for d in filtered if d.severity == severity]
    total = len(filtered)
    lim = max(1, min(int(limit), 200))
    off = max(0, int(offset))
    page = filtered[off : off + lim]
    return DecisionsListResponse(items=page, total=total, limit=lim, offset=off)


def build_decisions_impact(session: Session, *, refresh: bool = False) -> DecisionsImpactResponse:
    decisions = get_decisions(session, refresh=refresh)
    areas: dict[str, tuple[int, Literal["low", "medium", "high"]]] = {}
    for d in decisions:
        prefix = d.type
        ac, am = areas.get(prefix, (0, "low"))
        areas[prefix] = (ac + 1, _max_sev(am, d.severity))
    most_affected = [
        ImpactedArea(area=k, decision_count=v[0], max_severity=v[1]) for k, v in sorted(areas.items(), key=lambda x: -x[1][0])
    ]

    nf_inst: dict[str, float] = {}
    for d in decisions:
        for e in d.affected_entities:
            if e.startswith("narrative_function:"):
                nf = e.split(":", 1)[1]
                nf_inst[nf] = nf_inst.get(nf, 0.0) + (3.0 if d.severity == "high" else 2.0 if d.severity == "medium" else 1.0)
    clusters = [
        ClusterInstability(cluster_id=f"nf:{nf}", instability_score=round(min(100.0, sc * 4.0), 2), narrative_function=nf)
        for nf, sc in sorted(nf_inst.items(), key=lambda x: -x[1])[:12]
    ]

    cat_map: dict[str, tuple[str, list[str]]] = {}
    for d in decisions:
        for e in d.affected_entities:
            if e.startswith("category:"):
                cat = e.split(":", 1)[1]
                bucket = cat_map.setdefault(cat, ("Cobertura / hueco semántico", []))
                bucket[1].append(d.id)
            if e.startswith("subcategory:"):
                cat = e.split(":", 1)[1]
                bucket = cat_map.setdefault(cat, ("Subcategoría / redundancia", []))
                bucket[1].append(d.id)
    interventions = [
        CategoryIntervention(category=k, reason=v[0], related_decision_ids=sorted(set(v[1]))[:12])
        for k, v in sorted(cat_map.items(), key=lambda x: -len(x[1][1]))[:20]
    ]

    return DecisionsImpactResponse(
        most_affected_system_areas=most_affected,
        clusters_highest_instability=clusters,
        categories_requiring_intervention=interventions,
    )
