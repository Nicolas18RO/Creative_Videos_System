"""Memoria de uso y señales de refinamiento para recuperación (Fase 3 PRD, sin ML ni re-embeddings)."""

from __future__ import annotations

import hashlib
import logging
import math
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from aicos.config import get_config
from aicos.database.db import UsageEventRow
from aicos.models.schemas import SearchRequest, SearchRunContext

logger = logging.getLogger(__name__)


def query_fingerprint(req: SearchRequest) -> str:
    """Huella determinista de (consulta + función narrativa + contexto global opcional)."""
    q = " ".join((req.query or "").lower().split())
    nf = (req.narrative_function or "").strip().upper()
    gqe = " ".join((req.global_query_enrichment or "").lower().split())[:200]
    raw = f"{nf}|{gqe}|{q}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def _decay_factor(created_at: datetime | None, *, half_life_days: float) -> float:
    if created_at is None:
        return 1.0
    if created_at.tzinfo is not None:
        created_at = created_at.astimezone(timezone.utc).replace(tzinfo=None)
    now = datetime.utcnow()
    days = max(0.0, (now - created_at).total_seconds() / 86400.0)
    if half_life_days <= 1e-6:
        return 1.0
    return math.exp(-math.log(2.0) * days / half_life_days)


def record_search_pool(
    session: Session,
    *,
    req: SearchRequest,
    candidate_ids: list[str],
) -> None:
    """Persiste un evento de búsqueda con el pool de candidatos expuesto (sin embeddings)."""
    if not candidate_ids:
        return
    cfg = get_config().intelligence
    fp = query_fingerprint(req)
    nf = (req.narrative_function or "").strip().upper() or None
    row = UsageEventRow(
        id=str(uuid.uuid4()),
        event_type="search_pool",
        clip_id=None,
        query_fingerprint=fp,
        narrative_function=nf,
        scene_id=None,
        project_id=None,
        rank=None,
        weight=cfg.search_exposure_weight,
        payload={"candidate_ids": list(dict.fromkeys(candidate_ids))[:48]},
    )
    session.add(row)
    session.flush()


def record_audio_segment_search(
    session: Session,
    *,
    req: SearchRequest,
    context: SearchRunContext,
    candidate_ids: list[str],
) -> None:
    """Persiste búsqueda originada en segmento de ``analyze_audio`` (trazabilidad + decay)."""
    if not candidate_ids:
        return
    cfg = get_config().intelligence
    fp = query_fingerprint(req)
    nf = (req.narrative_function or "").strip().upper() or None
    payload: dict[str, Any] = {
        "audio_source": "analyze_audio",
        "correlation_id": context.correlation_id,
        "scene_index": context.scene_index,
        "concept": (context.concept or req.query or "")[:400],
        "candidate_ids": list(dict.fromkeys(candidate_ids))[:48],
    }
    row = UsageEventRow(
        id=str(uuid.uuid4()),
        event_type="audio_segment_search",
        clip_id=None,
        query_fingerprint=fp,
        narrative_function=nf,
        scene_id=None,
        project_id=context.correlation_id,
        rank=context.scene_index,
        weight=cfg.audio_segment_signal_weight,
        payload=payload,
    )
    session.add(row)
    session.flush()


def record_feedback_event(
    session: Session,
    *,
    scene_id: str,
    project_id: str | None,
    clip_id: str,
    accepted: bool,
    rank: int | None,
    narrative_function: str | None,
) -> None:
    """Registra feedback explícito para memoria de ranking."""
    cfg = get_config().intelligence
    w = cfg.feedback_positive_weight if accepted else cfg.feedback_negative_weight
    et = "feedback_yes" if accepted else "feedback_no"
    row = UsageEventRow(
        id=str(uuid.uuid4()),
        event_type=et,
        clip_id=clip_id,
        query_fingerprint=None,
        narrative_function=(narrative_function or "").strip().upper() or None,
        scene_id=scene_id,
        project_id=project_id,
        rank=rank,
        weight=w,
        payload=None,
    )
    session.add(row)
    session.flush()


def compute_audio_session_penalties(*, clip_ids: list[str], used_clip_ids: list[str]) -> dict[str, float]:
    """Penaliza clips ya usados en el mismo pase de análisis (repetición en voice-over)."""
    cfg = get_config().intelligence
    used = set(used_clip_ids)
    out: dict[str, float] = {}
    for cid in clip_ids:
        if cid in used:
            out[cid] = out.get(cid, 0.0) - float(cfg.audio_repeat_clip_penalty)
    return out


def compute_intelligence_boosts(
    session: Session,
    *,
    clip_ids: list[str],
    query_fp: str,
    narrative_function: str | None,
) -> dict[str, float]:
    """Agrega boosts por clip a partir de eventos recientes (determinista)."""
    if not clip_ids:
        return {}
    cfg = get_config().intelligence
    cutoff_naive = datetime.utcnow() - timedelta(days=int(cfg.event_lookback_days))
    stmt = select(UsageEventRow).where(UsageEventRow.created_at >= cutoff_naive)
    rows = list(session.scalars(stmt).all())

    clip_set = set(clip_ids)
    acc: dict[str, float] = {cid: 0.0 for cid in clip_ids}
    nf_key = (narrative_function or "").strip().upper() or None

    for ev in rows:
        decay = _decay_factor(ev.created_at, half_life_days=cfg.half_life_days)
        base_w = float(ev.weight or 0.0) * decay

        if ev.event_type in ("feedback_yes", "feedback_no") and ev.clip_id in clip_set:
            if nf_key and ev.narrative_function and ev.narrative_function != nf_key:
                base_w *= 0.35
            acc[ev.clip_id] = acc.get(ev.clip_id, 0.0) + base_w

        if ev.event_type in ("search_pool", "audio_segment_search") and ev.payload and isinstance(ev.payload, dict):
            ids = ev.payload.get("candidate_ids") or []
            if not isinstance(ids, list):
                continue
            overlap = [str(x) for x in ids if str(x) in clip_set]
            if not overlap:
                continue
            same_q = ev.query_fingerprint == query_fp
            base_wt = (
                cfg.audio_segment_signal_weight if ev.event_type == "audio_segment_search" else cfg.search_exposure_weight
            )
            for cid in overlap:
                bump = base_wt * decay * (1.35 if same_q else 1.0)
                if ev.event_type == "audio_segment_search" and same_q:
                    bump *= 1.08
                acc[cid] = acc.get(cid, 0.0) + bump / max(1, len(overlap))

    out: dict[str, float] = {}
    cap_hi = cfg.max_intelligence_boost
    cap_lo = cfg.min_intelligence_boost
    for cid in clip_ids:
        raw = acc.get(cid, 0.0)
        out[cid] = max(cap_lo, min(cap_hi, raw))
    return out


def refined_context_summary(session: Session, *, query_fp: str) -> dict[str, Any]:
    """Resumen explicable de memoria asociada a una huella (para trazabilidad)."""
    stmt = select(UsageEventRow).where(UsageEventRow.query_fingerprint == query_fp).limit(20)
    n = len(list(session.scalars(stmt).all()))
    return {"query_fingerprint": query_fp, "recent_matching_search_events": n}
