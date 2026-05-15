"""Tests Fase 6.7 — workspace de entrenamiento editorial."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

from dataclasses import replace

import pytest

from aicos.application.editorial_dataset.creative_timeline_builder_service import CreativeTimelineBuilderService
from aicos.application.editorial_training.editorial_training_workspace_service import EditorialTrainingWorkspaceService
from aicos.application.editorial_training.ports import EditorialStyleEmbeddingAttachPort
from aicos.config import AppConfig, EditorialTrainingWorkspaceConfig
from aicos.domain.editorial_dataset.entities import CreativeTimeline, CreativeStyleProfile, EditorialStyleSignals
from aicos.domain.editorial_training.entities import EditorialTrainingSessionStatus
from aicos.domain.editorial_training.rules import validate_correction_reward


class _FakePersistence:
    def __init__(self) -> None:
        self.store: dict[str, object] = {}

    def get_by_id(self, session, session_id: str):  # noqa: ARG002
        return self.store.get(session_id)

    def save(self, session, training: object) -> None:  # noqa: ARG002
        from aicos.domain.editorial_training.entities import EditorialTrainingSession

        assert isinstance(training, EditorialTrainingSession)
        self.store[training.session_id] = training


class _FakeTimelineRead:
    def __init__(self, timeline: CreativeTimeline | None) -> None:
        self._t = timeline

    def get_by_creative_id(self, session, creative_id: str):  # noqa: ARG002
        if self._t is None:
            return None
        return self._t if self._t.creative_id == creative_id else None


class _NoOpAttach(EditorialStyleEmbeddingAttachPort):
    def attach_if_configured(self, session, timeline: CreativeTimeline) -> CreativeTimeline:  # noqa: ARG002
        return timeline


def _minimal_timeline(cid: str) -> CreativeTimeline:
    sp = CreativeStyleProfile(0.5, 0.5, 0.5, 0.2, 0.3, 0.4, ())
    ss = EditorialStyleSignals(0.5, 0.5, (), 0.4)
    return CreativeTimeline(
        creative_id=cid,
        audio_path="",
        final_video_path="",
        timeline_scenes=(),
        style_profile=sp,
        style_signals=ss,
        created_at=datetime.now(timezone.utc),
    )


def test_validate_correction_reward_bounds() -> None:
    assert validate_correction_reward(2.0) == 1.0
    assert validate_correction_reward(-3.0) == -1.0


def test_create_session_roundtrip() -> None:
    app = AppConfig()
    store = _FakePersistence()
    mock_builder = MagicMock(spec=CreativeTimelineBuilderService)
    svc = EditorialTrainingWorkspaceService(
        workspace_cfg=EditorialTrainingWorkspaceConfig(enabled=True),
        app_cfg=app,
        persistence=store,
        timeline_builder=mock_builder,
        timeline_read=_FakeTimelineRead(None),
        human_feedback=None,
        style_embedding_attach=_NoOpAttach(),
    )
    s = svc.create_session(MagicMock(), creative_id="c99", project_id=None, final_video_path="/v/x.mp4", audio_path="")
    assert s.status == EditorialTrainingSessionStatus.DRAFT
    assert store.store[s.session_id].creative_id == "c99"


def test_commit_learning_calls_attach() -> None:
    app = AppConfig()
    store = _FakePersistence()
    mock_builder = MagicMock(spec=CreativeTimelineBuilderService)
    tl = _minimal_timeline("c88")
    attach = MagicMock(spec=EditorialStyleEmbeddingAttachPort)
    attach.attach_if_configured.side_effect = lambda session, t: t
    svc = EditorialTrainingWorkspaceService(
        workspace_cfg=EditorialTrainingWorkspaceConfig(enabled=True),
        app_cfg=app,
        persistence=store,
        timeline_builder=mock_builder,
        timeline_read=_FakeTimelineRead(tl),
        human_feedback=None,
        style_embedding_attach=attach,
    )
    s0 = svc.create_session(MagicMock(), creative_id="c88", project_id=None, final_video_path="", audio_path="")
    s1 = replace(s0, status=EditorialTrainingSessionStatus.AWAITING_HUMAN)
    store.save(MagicMock(), s1)
    svc.commit_learning(MagicMock(), s0.session_id)
    attach.attach_if_configured.assert_called_once()
    assert store.store[s0.session_id].status == EditorialTrainingSessionStatus.COMMITTED
