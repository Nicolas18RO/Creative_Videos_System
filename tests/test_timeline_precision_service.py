"""Tests aplicación Fase 6.8 — servicio de precisión."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

from aicos.application.editorial_dataset.ports import RawTimelineSceneInput
from aicos.application.editorial_training.timeline_precision_service import TimelinePrecisionService
from aicos.domain.editorial_dataset.entities import (
    CreativeStyleProfile,
    CreativeTimeline,
    EditorialStyleSignals,
    TimelineScene,
)
from aicos.domain.editorial_training.entities import EditorialTimelineAdjustment, EditorialTrainingSession
from aicos.domain.editorial_training.timeline_rules import SceneBoundary


class _MemAdjustments:
    def __init__(self) -> None:
        self._rows: dict[tuple[str, int], EditorialTimelineAdjustment] = {}

    def list_by_session(self, session, session_id: str):
        return tuple(v for (sid, _), v in self._rows.items() if sid == session_id)

    def upsert(self, session, adjustment: EditorialTimelineAdjustment) -> None:
        self._rows[(adjustment.session_id, adjustment.scene_index)] = adjustment


class _FakeTimelineRead:
    def __init__(self, timeline: CreativeTimeline | None) -> None:
        self._timeline = timeline

    def get_by_creative_id(self, session, creative_id: str):
        return self._timeline


class _FakeWorkspace:
    def __init__(self, session_entity: EditorialTrainingSession, timeline: CreativeTimeline) -> None:
        self._session = session_entity
        self._timeline = timeline
        self.submitted: tuple[RawTimelineSceneInput, ...] | None = None

    def get_session(self, session, session_id: str):
        return self._session if self._session.session_id == session_id else None

    def submit_timeline(self, session, session_id: str, raw_scenes):
        self.submitted = raw_scenes
        scenes = tuple(
            TimelineScene(
                scene_index=r.scene_index,
                clip_id=r.clip_id,
                start_time=r.start_time,
                end_time=r.end_time,
                duration=r.end_time - r.start_time,
                transition_type=r.transition_type,
                narrative_role=r.narrative_role,
                motion_intensity=r.motion_intensity,
                visual_energy=r.visual_energy,
                camera_type=r.camera_type,
                semantic_tags=r.semantic_tags,
                emotion_tags=r.emotion_tags,
            )
            for r in raw_scenes
        )
        self._timeline = replace(self._timeline, timeline_scenes=scenes)
        return self._timeline


def _timeline() -> CreativeTimeline:
    return CreativeTimeline(
        creative_id="cr1",
        audio_path="a.wav",
        final_video_path="v.mp4",
        timeline_scenes=(
            TimelineScene(
                scene_index=0,
                clip_id="c0",
                start_time=0.0,
                end_time=5.0,
                duration=5.0,
                transition_type="cut",
                narrative_role="HOOK",
                motion_intensity=0.5,
                visual_energy=0.5,
                camera_type="",
                semantic_tags=(),
                emotion_tags=(),
            ),
        ),
        style_profile=CreativeStyleProfile(0.5, 0.5, 0.5, 0.5, 0.5, 0.5, ()),
        style_signals=EditorialStyleSignals(0.5, 0.5, (), 0.5),
    )


def _session() -> EditorialTrainingSession:
    now = datetime.now(timezone.utc)
    return EditorialTrainingSession(
        session_id="s1",
        creative_id="cr1",
        project_id=None,
        status="awaiting_human",
        final_video_path="v.mp4",
        audio_path="a.wav",
        corrections=(),
        created_at=now,
        updated_at=now,
    )


def test_save_adjustments_preserves_auto_detected():
    tl = _timeline()
    ws = _FakeWorkspace(_session(), tl)
    adj = _MemAdjustments()
    svc = TimelinePrecisionService(timeline_read=_FakeTimelineRead(tl), workspace=ws, adjustments=adj)
    raw = (
        RawTimelineSceneInput(
            scene_index=0,
            clip_id="c0",
            start_time=0.05,
            end_time=4.95,
            transition_type="cut",
            narrative_role="HOOK",
            motion_intensity=0.5,
            visual_energy=0.5,
            camera_type="",
            semantic_tags=(),
            emotion_tags=(),
        ),
    )
    _, _, saved = svc.save_timeline_adjustments(None, "s1", raw)
    assert len(saved) == 1
    assert saved[0].auto_detected_start_time == 0.0
    assert saved[0].human_adjusted_start_time == 0.05


def test_validate_rejects_overlap():
    tl = _timeline()
    svc = TimelinePrecisionService(
        timeline_read=_FakeTimelineRead(tl),
        workspace=_FakeWorkspace(_session(), tl),
        adjustments=_MemAdjustments(),
    )
    boundaries = (
        SceneBoundary(0, 0.0, 5.0),
        SceneBoundary(1, 4.5, 8.0),
    )
    result = svc.validate_timeline_draft(boundaries)
    assert not result.valid
