"""Comandos y servicio de ingestión + cálculo de boosts para ranking (Fase 6.6)."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from aicos.application.human_feedback.ports import HumanFeedbackEventPersistencePort
from aicos.config import HumanFeedbackReinforcementConfig
from aicos.domain.human_feedback.entities import EditorialHumanFeedbackEvent
from aicos.domain.human_feedback.rules import HumanFeedbackAccumulationParams, accumulate_clip_boosts

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class IngestEditorialHumanFeedbackCommand:
    event_kind: str
    reward: float
    creative_id: str | None = None
    clip_id: str | None = None
    replaced_clip_id: str | None = None
    scene_index: int | None = None
    narrative_function: str | None = None
    transition_type: str | None = None
    query_fingerprint: str | None = None


class HumanFeedbackReinforcementService:
    def __init__(self, cfg: HumanFeedbackReinforcementConfig, store: HumanFeedbackEventPersistencePort) -> None:
        self._cfg = cfg
        self._store = store

    def ingest(self, session: Any, cmd: IngestEditorialHumanFeedbackCommand) -> str:
        if not self._cfg.enabled:
            raise ValueError("human_feedback_reinforcement_disabled")
        rk = max(-1.0, min(1.0, float(cmd.reward)))
        eid = str(uuid.uuid4())
        nf = (cmd.narrative_function or "").strip().upper() or None
        ev = EditorialHumanFeedbackEvent(
            id=eid,
            created_at=datetime.now(timezone.utc),
            event_kind=(cmd.event_kind or "generic").strip()[:48],
            reward=rk,
            creative_id=(cmd.creative_id or "").strip() or None,
            clip_id=(cmd.clip_id or "").strip() or None,
            replaced_clip_id=(cmd.replaced_clip_id or "").strip() or None,
            scene_index=cmd.scene_index,
            narrative_function=nf,
            transition_type=(cmd.transition_type or "").strip()[:48] or None,
            query_fingerprint=(cmd.query_fingerprint or "").strip()[:64] or None,
        )
        self._store.append(session, ev)
        logger.info(
            "[HumanFeedbackReinforcement] ingested id=%s kind=%s reward=%.3f clip=%s creative=%s",
            eid,
            ev.event_kind,
            rk,
            ev.clip_id or "",
            ev.creative_id or "",
        )
        return eid

    def compute_clip_boosts(
        self,
        session: Any,
        *,
        clip_ids: list[str],
        narrative_function: str | None,
        _query_fingerprint: str | None = None,
    ) -> dict[str, float]:
        if not self._cfg.enabled or not clip_ids or not self._cfg.apply_in_search:
            return {}
        since = datetime.now(timezone.utc) - timedelta(days=max(1, int(self._cfg.lookback_days)))
        events = self._store.list_since(session, since=since)
        params = HumanFeedbackAccumulationParams(
            now=datetime.now(timezone.utc),
            lookback_days=max(1, int(self._cfg.lookback_days)),
            half_life_days=float(self._cfg.half_life_days),
            signal_weight=float(self._cfg.signal_weight),
            swap_penalty_ratio=float(self._cfg.swap_penalty_ratio),
            narrative_mismatch_factor=float(self._cfg.narrative_mismatch_factor),
            max_boost_per_clip=float(self._cfg.max_boost_per_clip),
            min_boost_per_clip=float(self._cfg.min_boost_per_clip),
        )
        return accumulate_clip_boosts(
            events,
            frozenset(clip_ids),
            narrative_function,
            params,
        )
