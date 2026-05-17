"""Fusión de escenas adyacentes con auditoría y persistencia de timeline."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from aicos.application.editorial_dataset.ports import (
    CreativeTimelinePersistenceReadPort,
    CreativeTimelinePersistenceWritePort,
    RawTimelineSceneInput,
)
from aicos.application.editorial_review.ports import (
    EditorialSceneMergePersistencePort,
    EditorialSceneReviewPersistencePort,
)
from aicos.application.editorial_review.timeline_review_service import TimelineReviewService
from aicos.domain.editorial_dataset.entities import CreativeTimeline, TimelineScene
from aicos.domain.editorial_review.entities import EditorialSceneMergeRecord, EditorialSceneReviewState
from aicos.domain.editorial_review.enums import EditorialSceneReviewStatus
from aicos.domain.editorial_review.rules import cannot_merge_rejected_scene, merge_requires_adjacent_scenes
from aicos.domain.editorial_review.scene_merge import merge_timeline_scenes, scene_id_from_index

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class MergeScenesResult:
    resulting_scene_id: str
    resulting_scene_index: int
    merged_scene_ids: tuple[str, str]
    timeline: CreativeTimeline


class MergeScenesService:
    def __init__(
        self,
        *,
        timeline_read: CreativeTimelinePersistenceReadPort,
        timeline_write: CreativeTimelinePersistenceWritePort | None,
        review: TimelineReviewService,
        review_repo: EditorialSceneReviewPersistencePort,
        merge_repo: EditorialSceneMergePersistencePort,
        timeline_builder_submit: Any | None = None,
    ) -> None:
        self._timeline_read = timeline_read
        self._timeline_write = timeline_write
        self._review = review
        self._review_repo = review_repo
        self._merge_repo = merge_repo
        self._timeline_builder_submit = timeline_builder_submit

    def _active_scenes(
        self, session: Any, session_id: str, timeline: CreativeTimeline
    ) -> list[TimelineScene]:
        reviews = {r.scene_id: r for r in self._review_repo.list_by_session(session, session_id)}
        out: list[TimelineScene] = []
        for s in sorted(timeline.timeline_scenes, key=lambda x: x.scene_index):
            sid = scene_id_from_index(s.scene_index)
            st = reviews.get(sid)
            if st and st.status == EditorialSceneReviewStatus.MERGED:
                continue
            out.append(s)
        return out

    def merge_adjacent_scenes(
        self,
        session: Any,
        session_id: str,
        creative_id: str,
        scene_index_a: int,
        scene_index_b: int,
        *,
        reviewer: str = "human",
    ) -> MergeScenesResult:
        if not merge_requires_adjacent_scenes(scene_index_a, scene_index_b):
            raise ValueError("merge_requires_adjacent_scenes")
        timeline = self._timeline_read.get_by_creative_id(session, creative_id)
        if timeline is None:
            raise ValueError("creative_timeline_not_found")

        active = self._active_scenes(session, session_id, timeline)
        by_idx = {s.scene_index: s for s in active}
        if scene_index_a not in by_idx or scene_index_b not in by_idx:
            raise ValueError("timeline_scene_not_found")

        left_i, right_i = (
            (scene_index_a, scene_index_b) if scene_index_a < scene_index_b else (scene_index_b, scene_index_a)
        )
        left = by_idx[left_i]
        right = by_idx[right_i]

        for sc in (left, right):
            sid = scene_id_from_index(sc.scene_index)
            st = self._review.get_state(session, session_id, sid)
            if cannot_merge_rejected_scene(st.status):
                raise ValueError("cannot_merge_rejected_scene")

        new_index = left_i
        merged = merge_timeline_scenes(left, right, resulting_scene_index=new_index)
        resulting_id = scene_id_from_index(new_index)

        merge_rec = EditorialSceneMergeRecord(
            source_scene_a=scene_id_from_index(left_i),
            source_scene_b=scene_id_from_index(right_i),
            resulting_scene_id=resulting_id,
            session_id=session_id,
            created_at=datetime.now(timezone.utc),
        )
        self._merge_repo.save(session, merge_rec)

        self._review.set_scene_status(
            session,
            session_id,
            scene_id_from_index(left_i),
            status=EditorialSceneReviewStatus.MERGED,
            reviewer=reviewer,
            correction_reason="scene_merge",
            merged_into_scene_id=resulting_id,
        )
        self._review.set_scene_status(
            session,
            session_id,
            scene_id_from_index(right_i),
            status=EditorialSceneReviewStatus.MERGED,
            reviewer=reviewer,
            correction_reason="scene_merge",
            merged_into_scene_id=resulting_id,
        )
        self._review.set_scene_status(
            session,
            session_id,
            resulting_id,
            status=EditorialSceneReviewStatus.PENDING,
            reviewer=reviewer,
            correction_reason="merge_result",
        )

        new_active: list[TimelineScene] = []
        for s in active:
            if s.scene_index in (left_i, right_i):
                continue
            new_active.append(s)
        new_active.append(merged)
        new_active.sort(key=lambda x: x.scene_index)

        reindexed: list[TimelineScene] = []
        for i, s in enumerate(new_active):
            reindexed.append(
                TimelineScene(
                    scene_index=i,
                    clip_id=s.clip_id,
                    start_time=s.start_time,
                    end_time=s.end_time,
                    duration=s.duration,
                    transition_type=s.transition_type,
                    narrative_role=s.narrative_role,
                    motion_intensity=s.motion_intensity,
                    visual_energy=s.visual_energy,
                    camera_type=s.camera_type,
                    semantic_tags=s.semantic_tags,
                    emotion_tags=s.emotion_tags,
                )
            )

        raw = tuple(self._scene_to_raw(s) for s in reindexed)
        if self._timeline_builder_submit is not None:
            updated = self._timeline_builder_submit(
                session,
                session_id,
                creative_id,
                raw,
                timeline.audio_path,
                timeline.final_video_path,
            )
        else:
            updated = timeline

        logger.info(
            "[EditorialReview] merged %s+%s -> %s session=%s",
            left_i,
            right_i,
            resulting_id,
            session_id,
        )
        return MergeScenesResult(
            resulting_scene_id=resulting_id,
            resulting_scene_index=new_index,
            merged_scene_ids=(scene_id_from_index(left_i), scene_id_from_index(right_i)),
            timeline=updated,
        )

    @staticmethod
    def _scene_to_raw(s: TimelineScene) -> RawTimelineSceneInput:
        return RawTimelineSceneInput(
            scene_index=s.scene_index,
            clip_id=s.clip_id,
            start_time=s.start_time,
            end_time=s.end_time,
            transition_type=s.transition_type,
            narrative_role=s.narrative_role,
            motion_intensity=s.motion_intensity,
            visual_energy=s.visual_energy,
            camera_type=s.camera_type,
            semantic_tags=s.semantic_tags,
            emotion_tags=s.emotion_tags,
        )
