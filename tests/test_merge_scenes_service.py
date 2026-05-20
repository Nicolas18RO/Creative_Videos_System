"""Tests de fusión real de escenas (Fase 6.7.X)."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from typing import Any

from aicos.application.editorial_review.merge_scenes_service import MergeScenesService
from aicos.application.editorial_review.timeline_review_service import TimelineReviewService
from aicos.domain.editorial_dataset.entities import CreativeTimeline, TimelineScene
from aicos.domain.editorial_review.entities import EditorialSceneMergeRecord, EditorialSceneReviewState
from aicos.domain.editorial_review.enums import EditorialSceneReviewStatus
from aicos.domain.editorial_review.rules import scenes_adjacent_in_ordered_list


def _scene(idx: int, start: float, end: float, role: str = "NATURAL") -> TimelineScene:
    return TimelineScene(
        scene_index=idx,
        clip_id=f"c{idx}",
        start_time=start,
        end_time=end,
        duration=end - start,
        transition_type="cut",
        narrative_role=role,
        motion_intensity=0.5,
        visual_energy=0.5,
        camera_type="",
        semantic_tags=(),
        emotion_tags=(),
    )


class MemTimeline:
    def __init__(self, timeline: CreativeTimeline) -> None:
        self._tl = timeline

    def get_by_creative_id(self, session: Any, creative_id: str) -> CreativeTimeline | None:
        return self._tl

    def save(self, session: Any, timeline: CreativeTimeline) -> None:
        self._tl = timeline


class MemReview:
    def __init__(self) -> None:
        self._rows: dict[tuple[str, str], EditorialSceneReviewState] = {}

    def list_by_session(self, session: Any, session_id: str) -> tuple[EditorialSceneReviewState, ...]:
        return tuple(v for (sid, _), v in self._rows.items() if sid == session_id)

    def get(self, session: Any, session_id: str, scene_id: str) -> EditorialSceneReviewState | None:
        return self._rows.get((session_id, scene_id))

    def upsert(self, session: Any, session_id: str, state: EditorialSceneReviewState) -> None:
        self._rows[(session_id, state.scene_id)] = state


class MemMerge:
    def save(self, session: Any, record: EditorialSceneMergeRecord) -> None:
        pass


def test_adjacent_in_active_list_not_numeric_gap():
    indices = (0, 2, 5)
    assert scenes_adjacent_in_ordered_list(indices, 0, 2)
    assert not scenes_adjacent_in_ordered_list(indices, 0, 5)


def test_merge_reduces_scene_count_and_extends_duration():
    tl = CreativeTimeline(
        creative_id="c1",
        audio_path="a.wav",
        final_video_path="v.mp4",
        timeline_scenes=(
            _scene(0, 0, 2, "HOOK"),
            _scene(1, 2, 4, "PROBLEM"),
            _scene(2, 4, 6, "CTA"),
        ),
        style_profile=None,  # type: ignore[arg-type]
        style_signals=None,  # type: ignore[arg-type]
        editorial_patterns=(),
        hook_detection=(),
        created_at=datetime.now(timezone.utc),
        dataset_version=1,
    )
    # minimal style - need real profile
    from aicos.domain.editorial_dataset.entities import CreativeStyleProfile, EditorialStyleSignals

    tl = replace(
        tl,
        style_profile=CreativeStyleProfile(
            hook_intensity=0.5,
            average_pacing=0.5,
            motion_density=0.5,
            transition_density=0.5,
            narrative_aggressiveness=0.5,
            visual_dynamism=0.5,
            cinematic_style_tags=(),
        ),
        style_signals=EditorialStyleSignals(
            pacing_score=0.5,
            hook_strength=0.5,
            emotional_curve=(),
            visual_dynamism=0.5,
        ),
    )

    timeline_repo = MemTimeline(tl)
    submitted: list = []

    def submit(session, session_id, creative_id, raw, audio_path, final_video_path):
        submitted.append(raw)
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
            for r in raw
        )
        return replace(tl, timeline_scenes=scenes)

    reviews = MemReview()
    svc = MergeScenesService(
        timeline_read=timeline_repo,
        timeline_write=timeline_repo,
        review=TimelineReviewService(persistence=reviews),
        review_repo=reviews,
        merge_repo=MemMerge(),
        timeline_builder_submit=submit,
    )
    result = svc.merge_adjacent_scenes(None, "sess", "c1", 0, 1)
    assert len(result.timeline.timeline_scenes) == 2
    merged = result.timeline.timeline_scenes[0]
    assert merged.end_time - merged.start_time == 4.0
    assert merged.narrative_role == "HOOK"
