"""Reglas puras: decaimiento temporal y agregación de boosts por clip (Fase 6.6)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from aicos.domain.human_feedback.entities import EditorialHumanFeedbackEvent


def time_decay_multiplier(created_at: datetime, *, now: datetime, half_life_days: float) -> float:
    """Decaimiento exponencial coherente con la memoria de uso (mitad por ``half_life_days``)."""
    if half_life_days <= 1e-9:
        return 1.0
    ca = created_at
    if ca.tzinfo is not None:
        ca = ca.astimezone(timezone.utc).replace(tzinfo=None)
    nw = now
    if nw.tzinfo is not None:
        nw = nw.astimezone(timezone.utc).replace(tzinfo=None)
    days = max(0.0, (nw - ca).total_seconds() / 86400.0)
    return math.exp(-math.log(2.0) * days / half_life_days)


def _narrative_match_multiplier(
    event_nf: str | None,
    context_nf: str | None,
    *,
    mismatch_factor: float,
) -> float:
    ev = (event_nf or "").strip().upper() or None
    ctx = (context_nf or "").strip().upper() or None
    if not ctx or not ev:
        return 1.0
    if ev == ctx:
        return 1.0
    return max(0.0, min(1.0, float(mismatch_factor)))


@dataclass(frozen=True, slots=True)
class HumanFeedbackAccumulationParams:
    now: datetime
    lookback_days: int
    half_life_days: float
    signal_weight: float
    swap_penalty_ratio: float
    narrative_mismatch_factor: float
    max_boost_per_clip: float
    min_boost_per_clip: float


def accumulate_clip_boosts(
    events: tuple[EditorialHumanFeedbackEvent, ...],
    clip_ids: frozenset[str],
    narrative_function_context: str | None,
    params: HumanFeedbackAccumulationParams,
) -> dict[str, float]:
    """Agrega contribuciones por ``clip_id`` (y penaliza ``replaced_clip_id`` en swaps)."""
    if not clip_ids:
        return {}
    cutoff = params.now - timedelta(days=max(1, int(params.lookback_days)))
    acc: dict[str, float] = {cid: 0.0 for cid in clip_ids}
    for ev in events:
        if ev.created_at < cutoff:
            continue
        decay = time_decay_multiplier(ev.created_at, now=params.now, half_life_days=params.half_life_days)
        nf_mul = _narrative_match_multiplier(
            ev.narrative_function,
            narrative_function_context,
            mismatch_factor=params.narrative_mismatch_factor,
        )
        base = float(ev.reward) * float(params.signal_weight) * decay * nf_mul
        cid = ev.clip_id
        if cid and cid in acc:
            acc[cid] = acc.get(cid, 0.0) + base
        rep = ev.replaced_clip_id
        if rep and rep in acc and cid and cid != rep:
            acc[rep] = acc.get(rep, 0.0) - base * float(params.swap_penalty_ratio)
    hi = float(params.max_boost_per_clip)
    lo = float(params.min_boost_per_clip)
    out: dict[str, float] = {}
    for cid, raw in acc.items():
        out[cid] = max(lo, min(hi, raw))
    return out
