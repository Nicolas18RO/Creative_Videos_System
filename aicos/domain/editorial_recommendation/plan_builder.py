"""Construcción pura del plan editorial a partir del timeline y memoria de estilo."""

from __future__ import annotations

from aicos.domain.editorial_dataset.entities import CreativeTimeline
from aicos.domain.editorial_recommendation.entities import (
    ClipSearchContextHint,
    EditorialRecommendationItem,
    EditorialRecommendationPlan,
    StyleMemoryPeerRef,
)


def _norm_role(role: str) -> str:
    return (role or "").strip().lower()


def _narrative_followup(last_role: str) -> tuple[str, str, float] | None:
    """Devuelve (summary, detail, confidence) o None si no hay señal clara."""
    lr = _norm_role(last_role)
    if not lr:
        return None
    table: dict[str, tuple[str, str, float]] = {
        "hook": (
            "Tras el hook, abre cuerpo o prueba social",
            "El rol actual sugiere apertura; prioriza clips de cuerpo informativo o prueba "
            "antes de subir de nuevo la energía visual.",
            0.74,
        ),
        "opening": (
            "Tras apertura, refuerza promesa o beneficio",
            "Mantén coherencia con el tono del hook; evita saltos bruscos de pacing en la siguiente escena.",
            0.68,
        ),
        "body": (
            "En tramo central, diversifica ángulo o emoción",
            "Alterna densidad de movimiento respecto a la escena previa para evitar fatiga visual.",
            0.62,
        ),
        "middle": (
            "En tramo central, refuerza prueba o detalle",
            "Introduce variación semántica (nuevo sub-tema) sin romper la promesa del inicio.",
            0.62,
        ),
        "payoff": (
            "Antes del payoff, prepara tensión o contraste",
            "Acerca evidencia concreta o contraste emocional que justifique el cierre.",
            0.7,
        ),
        "reveal": (
            "Tras revelación, ancla credibilidad",
            "Sostén la revelación con clip más estable (menos corte) o testimonio visual.",
            0.66,
        ),
        "cta": (
            "En CTA, simplifica estímulo visual",
            "Reduce complejidad de fondo; prioriza claridad de mensaje y legibilidad.",
            0.72,
        ),
        "outro": (
            "Cierre: coherencia de marca",
            "Mantén tags visuales alineados con el inicio del creativo para sensación de pieza única.",
            0.58,
        ),
    }
    tokens = set(lr.replace("-", " ").replace("_", " ").split())
    priority = ("hook", "opening", "cta", "outro", "payoff", "reveal", "body", "middle")
    for key in priority:
        if key in tokens and key in table:
            return table[key]
    return (
        "Continúa el arco narrativo con contraste moderado",
        f"Rol de escena «{last_role}»; alterna energía o densidad de corte respecto a la anterior.",
        0.52,
    )


def _pacing_item(
    anchor: CreativeTimeline, *, high: float, low: float
) -> EditorialRecommendationItem | None:
    ps = float(anchor.style_signals.pacing_score)
    if ps >= high:
        return EditorialRecommendationItem(
            recommendation_id="pacing_high",
            kind="pacing",
            summary="Pacing alto: refuerza legibilidad en el siguiente bloque",
            detail="El score de pacing sugiere ritmo sostenido; compensa con tomas más claras o "
            "pausas semánticas breves para no saturar.",
            confidence=min(0.95, 0.55 + (ps - high) * 0.8),
            sources=("style_signals.pacing_score",),
        )
    if ps <= low:
        return EditorialRecommendationItem(
            recommendation_id="pacing_low",
            kind="pacing",
            summary="Pacing bajo: puedes subir energía o contraste",
            detail="Hay margen para acelerar con cortes más frecuentes o mayor intensidad de movimiento.",
            confidence=min(0.9, 0.5 + (low - ps) * 0.7),
            sources=("style_signals.pacing_score",),
        )
    return None


def _pattern_item(anchor: CreativeTimeline) -> EditorialRecommendationItem | None:
    if not anchor.editorial_patterns:
        return None
    best = max(anchor.editorial_patterns, key=lambda p: p.frequency * p.confidence_score)
    seq = " → ".join(best.pattern_sequence[:8])
    if len(best.pattern_sequence) > 8:
        seq += " → …"
    return EditorialRecommendationItem(
        recommendation_id=f"pattern_{best.pattern_id}",
        kind="pattern",
        summary=f"Patrón editorial «{best.pattern_type}»",
        detail=f"Secuencia observada (frecuencia {best.frequency:.2f}): {seq}. "
        f"Reutilízalo como plantilla al buscar el siguiente clip.",
        confidence=max(0.35, min(0.9, best.confidence_score)),
        sources=("editorial_patterns", best.pattern_id),
    )


def _hook_item(anchor: CreativeTimeline) -> EditorialRecommendationItem | None:
    if not anchor.hook_detection:
        return None
    h0 = anchor.hook_detection[0]
    reasons = "; ".join(h0.reasons[:4]) if h0.reasons else "señal de apertura"
    return EditorialRecommendationItem(
        recommendation_id="hook_window",
        kind="hook",
        summary="Ventana de hook detectada en apertura",
        detail=f"Fuerza {h0.hook_strength:.2f} entre {h0.window_start:.1f}s y {h0.window_end:.1f}s. {reasons}",
        confidence=min(0.88, 0.45 + float(h0.hook_strength) * 0.4),
        sources=("pattern_engine_report.hooks",),
    )


def _style_memory_item(peers: tuple[StyleMemoryPeerRef, ...]) -> EditorialRecommendationItem | None:
    if not peers:
        return None
    top = ", ".join(f"{p.creative_id} ({p.hybrid_score:.2f})" for p in peers[:5])
    return EditorialRecommendationItem(
        recommendation_id="style_memory",
        kind="style_memory",
        summary="Memoria editorial: creativos de estilo afín",
        detail=f"Creativos similares para reutilizar ritmo/estructura: {top}. "
        "Revisa sus timelines como referencia de montaje.",
        confidence=min(0.92, 0.5 + peers[0].hybrid_score * 0.35),
        sources=tuple(f"style_peer:{p.creative_id}" for p in peers[:8]),
    )


def _clip_hint(anchor: CreativeTimeline, last_role_norm: str) -> ClipSearchContextHint | None:
    parts: list[str] = []
    tags = list(anchor.style_profile.cinematic_style_tags[:6])
    if tags:
        parts.append("Estilo: " + ", ".join(tags))
    if anchor.timeline_scenes:
        last = anchor.timeline_scenes[-1]
        st = list(last.semantic_tags[:5])
        et = list(last.emotion_tags[:4])
        if st:
            parts.append("Última escena (semántica): " + ", ".join(st))
        if et:
            parts.append("Emoción reciente: " + ", ".join(et))
    query_line = ". ".join(parts) if parts else f"Continuidad creativo {anchor.creative_id}"
    enrich = (
        "[AICOS editorial 6.5] " + query_line + ". Prioriza coherencia con el arco ya montado; "
        "evita repetir el mismo subtipo si el pacing es alto."
    )
    nf: str | None = None
    lr = last_role_norm
    if "hook" in lr or "opening" in lr:
        nf = "HOOK"
    elif "cta" in lr or "outro" in lr:
        nf = "CTA"
    elif lr:
        nf = "BODY"
    is_hook = "hook" in lr or "opening" in lr
    sem_list: list[str] = []
    for s in anchor.timeline_scenes[-2:]:
        for t in s.semantic_tags:
            if t and t not in sem_list:
                sem_list.append(t)
            if len(sem_list) >= 12:
                break
    sem = tuple(sem_list[:12])
    return ClipSearchContextHint(
        query_line=query_line,
        global_query_enrichment=enrich,
        narrative_function_hint=nf,
        is_hook_context=is_hook,
        semantic_tags=sem,
    )


def build_editorial_recommendation_plan(
    anchor: CreativeTimeline,
    style_peers: tuple[StyleMemoryPeerRef, ...],
    *,
    pacing_high_threshold: float = 0.72,
    pacing_low_threshold: float = 0.35,
) -> EditorialRecommendationPlan:
    """Ensambla ítems editoriales y el puente semántico hacia búsqueda de clips."""
    items: list[EditorialRecommendationItem] = []
    sm = _style_memory_item(style_peers)
    if sm:
        items.append(sm)
    last_role = ""
    if anchor.timeline_scenes:
        last_role = anchor.timeline_scenes[-1].narrative_role
    nf = _narrative_followup(last_role)
    if nf:
        summary, detail, conf = nf
        items.append(
            EditorialRecommendationItem(
                recommendation_id="narrative_followup",
                kind="narrative",
                summary=summary,
                detail=detail,
                confidence=conf,
                sources=("timeline.last_scene.narrative_role",),
            )
        )
    pi = _pacing_item(anchor, high=pacing_high_threshold, low=pacing_low_threshold)
    if pi:
        items.append(pi)
    hi = _hook_item(anchor)
    if hi:
        items.append(hi)
    pat = _pattern_item(anchor)
    if pat:
        items.append(pat)
    hint = _clip_hint(anchor, _norm_role(last_role))
    if hint:
        items.append(
            EditorialRecommendationItem(
                recommendation_id="clip_search_bridge",
                kind="clip_search",
                summary="Contexto sugerido para búsqueda semántica de clips",
                detail="Usa `query_line` como base de `query` y `global_query_enrichment` en SearchRequest "
                "para alinear el retrieval con este creativo.",
                confidence=0.55,
                sources=("clip_search_hint",),
            )
        )
    return EditorialRecommendationPlan(
        anchor_creative_id=anchor.creative_id,
        items=tuple(items),
        clip_search_hint=hint,
        style_memory_peers=style_peers,
    )
