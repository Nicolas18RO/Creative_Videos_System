"""Tests Fase 6.6 — refuerzo por feedback humano editorial."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from aicos.application.human_feedback.human_feedback_reinforcement_service import (
    HumanFeedbackReinforcementService,
    IngestEditorialHumanFeedbackCommand,
)
from aicos.config import HumanFeedbackReinforcementConfig
from aicos.domain.human_feedback.entities import EditorialHumanFeedbackEvent
from aicos.domain.human_feedback.rules import (
    HumanFeedbackAccumulationParams,
    accumulate_clip_boosts,
    time_decay_multiplier,
)


class _MemStore:
    def __init__(self) -> None:
        self.rows: list[EditorialHumanFeedbackEvent] = []

    def append(self, session, event: EditorialHumanFeedbackEvent) -> None:  # noqa: ARG002
        self.rows.append(event)

    def list_since(self, session, *, since: datetime) -> tuple[EditorialHumanFeedbackEvent, ...]:  # noqa: ARG002
        return tuple(e for e in self.rows if e.created_at >= since)


def test_time_decay_non_increasing() -> None:
    t0 = datetime(2024, 1, 1, tzinfo=timezone.utc)
    t1 = t0 + timedelta(days=10)
    d0 = time_decay_multiplier(t0, now=t1, half_life_days=5.0)
    d1 = time_decay_multiplier(t0, now=t1 + timedelta(days=20), half_life_days=5.0)
    assert d1 < d0


def test_accumulate_clip_boosts_positive_reward() -> None:
    now = datetime(2025, 6, 1, 12, 0, tzinfo=timezone.utc)
    ev = EditorialHumanFeedbackEvent(
        id="1",
        created_at=now - timedelta(days=1),
        event_kind="clip_accept",
        reward=1.0,
        creative_id=None,
        clip_id="c1",
        replaced_clip_id=None,
        scene_index=0,
        narrative_function="HOOK",
        transition_type=None,
        query_fingerprint=None,
    )
    params = HumanFeedbackAccumulationParams(
        now=now,
        lookback_days=30,
        half_life_days=30.0,
        signal_weight=0.1,
        swap_penalty_ratio=0.5,
        narrative_mismatch_factor=0.35,
        max_boost_per_clip=1.0,
        min_boost_per_clip=-1.0,
    )
    out = accumulate_clip_boosts((ev,), frozenset({"c1", "c2"}), "HOOK", params)
    assert out["c1"] > 0
    assert out["c2"] == 0.0


def test_accumulate_swap_penalizes_replaced() -> None:
    now = datetime(2025, 6, 1, 12, 0, tzinfo=timezone.utc)
    ev = EditorialHumanFeedbackEvent(
        id="2",
        created_at=now - timedelta(hours=2),
        event_kind="clip_swap",
        reward=0.8,
        creative_id="cr1",
        clip_id="new_clip",
        replaced_clip_id="old_clip",
        scene_index=1,
        narrative_function="BODY",
        transition_type=None,
        query_fingerprint=None,
    )
    params = HumanFeedbackAccumulationParams(
        now=now,
        lookback_days=30,
        half_life_days=30.0,
        signal_weight=0.1,
        swap_penalty_ratio=0.5,
        narrative_mismatch_factor=0.35,
        max_boost_per_clip=1.0,
        min_boost_per_clip=-1.0,
    )
    out = accumulate_clip_boosts((ev,), frozenset({"new_clip", "old_clip"}), "BODY", params)
    assert out["new_clip"] > 0
    assert out["old_clip"] < 0


def test_service_ingest_and_boost() -> None:
    cfg = HumanFeedbackReinforcementConfig(
        enabled=True,
        apply_in_search=True,
        signal_weight=0.2,
        lookback_days=7,
        half_life_days=30.0,
        max_boost_per_clip=0.5,
        min_boost_per_clip=-0.5,
    )
    store = _MemStore()
    svc = HumanFeedbackReinforcementService(cfg, store)
    cfg_off = HumanFeedbackReinforcementConfig(enabled=False)
    svc_off = HumanFeedbackReinforcementService(cfg_off, store)
    with pytest.raises(ValueError, match="human_feedback_reinforcement_disabled"):
        svc_off.ingest(
            MagicMock(),
            IngestEditorialHumanFeedbackCommand(event_kind="x", reward=0.5),
        )
    cmd = IngestEditorialHumanFeedbackCommand(
        event_kind="clip_accept", reward=1.0, clip_id="z1", narrative_function="HOOK"
    )
    svc.ingest(MagicMock(), cmd)
    boosts = svc.compute_clip_boosts(MagicMock(), clip_ids=["z1"], narrative_function="HOOK")
    assert boosts.get("z1", 0) > 0