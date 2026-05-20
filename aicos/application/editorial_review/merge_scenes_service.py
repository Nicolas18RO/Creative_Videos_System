"""Fusión de escenas adyacentes con auditoría y persistencia de timeline."""

from __future__ import annotations

import logging
from dataclasses import dataclass, replace
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
from aicos.domain.editorial_review.rules import cannot_merge_rejected_scene, scenes_adjacent_in_ordered_list
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
        semantic_intent_merge: Any | None = None,
    ) -> None:
        self._timeline_read = timeline_read
        self._timeline_write = timeline_write
        self._review = review
        self._review_repo = review_repo
        self._merge_repo = merge_repo
        self._timeline_builder_submit = timeline_builder_submit
        self._semantic_intent_merge = semantic_intent_merge

    def _active_scenes(
        self, session: Any, session_id: str, timeline: CreativeTimeline
    ) -> list[TimelineScene]:
        reviews = {r.scene_id: r for r in self._review_repo.list_by_session(session, session_id)}
        out: list[TimelineScene] = []
        for s in sorted(timeline.timeline_scenes, key=lambda x: x.start_time):
            sid = scene_id_from_index(s.scene_index)
            st = reviews.get(sid)
            if st and st.status == EditorialSceneReviewStatus.MERGED:
                continue
            out.append(s)
        return out

    def _reindex_reviews(
        self,
        session: Any,
        session_id: str,
        *,
        left_i: int,
        right_i: int,
        merged_pos: int,
        survivors: list[TimelineScene],
        old_to_new: dict[int, int],
        reviewer: str,
    ) -> None:
        """Remapea estados de revisión a los nuevos índices 0..n-1."""
        for sc in survivors:
            old_sid = scene_id_from_index(sc.scene_index)
            new_i = old_to_new.get(sc.scene_index)
            if new_i is None:
                continue
            st = self._review.get_state(session, session_id, old_sid)
            self._review_repo.upsert(
                session,
                session_id,
                replace(st, scene_id=scene_id_from_index(new_i), merged_into_scene_id=None),
            )

        merged_sid = scene_id_from_index(merged_pos)
        for src_i in (left_i, right_i):
            if src_i == merged_pos:
                continue
            self._review.set_scene_status(
                session,
                session_id,
                scene_id_from_index(src_i),
                status=EditorialSceneReviewStatus.MERGED,
                reviewer=reviewer,
                correction_reason="scene_merge",
                merged_into_scene_id=merged_sid,
            )
        self._review_repo.upsert(
            session,
            session_id,
            EditorialSceneReviewState(
                scene_id=merged_sid,
                status=EditorialSceneReviewStatus.PENDING,
                reviewed_at=datetime.now(timezone.utc),
                reviewer=reviewer,
                correction_reason="merge_result",
                merged_into_scene_id=None,
                confidence_override=None,
                notes="",
            ),
        )

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
        timeline = self._timeline_read.get_by_creative_id(session, creative_id)
        if timeline is None:
            raise ValueError("creative_timeline_not_found")

        active = self._active_scenes(session, session_id, timeline)
        ordered_indices = tuple(s.scene_index for s in active)
        if not scenes_adjacent_in_ordered_list(ordered_indices, scene_index_a, scene_index_b):
            raise ValueError("merge_requires_adjacent_scenes")

        by_idx = {s.scene_index: s for s in active}
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

        merged = merge_timeline_scenes(left, right, resulting_scene_index=left_i)

        merge_rec = EditorialSceneMergeRecord(
            source_scene_a=scene_id_from_index(left_i),
            source_scene_b=scene_id_from_index(right_i),
            resulting_scene_id=scene_id_from_index(left_i),
            session_id=session_id,
            created_at=datetime.now(timezone.utc),
        )
        self._merge_repo.save(session, merge_rec)

        survivors = [s for s in active if s.scene_index not in (left_i, right_i)]
        new_active = [*survivors, merged]
        new_active.sort(key=lambda s: s.start_time)

        old_to_new: dict[int, int] = {}
        reindexed: list[TimelineScene] = []
        merged_pos = 0
        for new_i, s in enumerate(new_active):
            old_to_new[s.scene_index] = new_i
            base = merged if s.scene_index == left_i else s
            if s.scene_index == left_i:
                merged_pos = new_i
            reindexed.append(
                replace(
                    base,
                    scene_index=new_i,
                    duration=max(0.0, base.end_time - base.start_time),
                )
            )

        self._reindex_reviews(
            session,
            session_id,
            left_i=left_i,
            right_i=right_i,
            merged_pos=merged_pos,
            survivors=survivors,
            old_to_new=old_to_new,
            reviewer=reviewer,
        )

        if self._semantic_intent_merge is not None:
            self._semantic_intent_merge(
                session,
                session_id,
                source_scene_index_a=left_i,
                source_scene_index_b=right_i,
                merged_scene=reindexed[merged_pos],
                old_to_new_index=old_to_new,
            )

        raw = tuple(self._scene_to_raw(s) for s in reindexed)
        if self._timeline_builder_submit is not None:
            updated = self._timeline_builder_submit(session, session_id, creative_id, raw, timeline.audio_path, timeline.final_video_path)
        elif self._timeline_write is not None:
            updated = replace(timeline, timeline_scenes=tuple(reindexed))
            self._timeline_write.save(session, updated)
        else:
            updated = replace(timeline, timeline_scenes=tuple(reindexed))

        resulting_id = scene_id_from_index(merged_pos)
        logger.info(
            "[EditorialReview] merged %s+%s -> pos=%s session=%s scenes=%s",
            left_i,
            right_i,
            merged_pos,
            session_id,
            len(reindexed),
        )
        return MergeScenesResult(
            resulting_scene_id=resulting_id,
            resulting_scene_index=merged_pos,
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
