"""Servicio de edición precisa de timeline (Fase 6.8)."""

from __future__ import annotations

import logging
from typing import Any

from aicos.application.editorial_dataset.ports import (
    CreativeTimelinePersistenceReadPort,
    RawTimelineSceneInput,
)
from aicos.application.editorial_training.logging_utils import (
    log_merge_preview,
    log_timeline_trim,
    log_timeline_validation,
)
from aicos.application.editorial_training.ports import EditorialTimelineAdjustmentPersistencePort
from aicos.application.editorial_training.editorial_training_workspace_service import (
    EditorialTrainingWorkspaceService,
)
from aicos.domain.editorial_dataset.entities import CreativeTimeline, TimelineScene
from aicos.domain.editorial_training.entities import EditorialTimelineAdjustment
from aicos.domain.editorial_training.merge_preview import MergePreviewResult, build_merge_preview
from aicos.domain.editorial_training.timeline_rules import (
    SceneBoundary,
    TimelineValidationResult,
    validate_scene_boundaries,
)

logger = logging.getLogger(__name__)


class TimelinePrecisionService:
    def __init__(
        self,
        *,
        timeline_read: CreativeTimelinePersistenceReadPort,
        workspace: EditorialTrainingWorkspaceService,
        adjustments: EditorialTimelineAdjustmentPersistencePort,
    ) -> None:
        self._timeline_read = timeline_read
        self._workspace = workspace
        self._adjustments = adjustments

    def validate_timeline_draft(
        self,
        scenes: tuple[SceneBoundary, ...],
        *,
        timeline_duration: float | None = None,
        session_id: str = "",
    ) -> TimelineValidationResult:
        result = validate_scene_boundaries(scenes, timeline_duration=timeline_duration)
        overlap = any(i.code == "overlap" for i in result.issues)
        log_timeline_validation(
            overlap_detected=overlap,
            issue_count=len(result.issues),
            session_id=session_id,
        )
        return result

    def merge_preview(
        self,
        session: Any,
        creative_id: str,
        scene_index_a: int,
        scene_index_b: int,
    ) -> MergePreviewResult:
        timeline = self._timeline_read.get_by_creative_id(session, creative_id)
        if timeline is None:
            raise ValueError("creative_timeline_not_found")
        by_idx = {s.scene_index: s for s in timeline.timeline_scenes}
        if scene_index_a not in by_idx or scene_index_b not in by_idx:
            raise ValueError("timeline_scene_not_found")
        left_i, right_i = (
            (scene_index_a, scene_index_b) if scene_index_a < scene_index_b else (scene_index_b, scene_index_a)
        )
        preview = build_merge_preview(by_idx[left_i], by_idx[right_i])
        log_merge_preview(
            source=f"{left_i}+{right_i}",
            duration=preview.total_duration,
            boundary=preview.removed_boundary_time,
        )
        return preview

    def save_timeline_adjustments(
        self,
        session: Any,
        session_id: str,
        raw_scenes: tuple[RawTimelineSceneInput, ...],
        *,
        adjustment_reason: str = "human_trim",
        timeline_duration: float | None = None,
    ) -> tuple[CreativeTimeline, TimelineValidationResult, tuple[EditorialTimelineAdjustment, ...]]:
        training = self._workspace.get_session(session, session_id)
        if training is None:
            raise ValueError("editorial_training_session_not_found")

        boundaries = tuple(
            SceneBoundary(scene_index=s.scene_index, start_time=s.start_time, end_time=s.end_time)
            for s in sorted(raw_scenes, key=lambda x: x.scene_index)
        )
        validation = self.validate_timeline_draft(
            boundaries,
            timeline_duration=timeline_duration,
            session_id=session_id,
        )
        if not validation.valid:
            raise ValueError("timeline_validation_failed")

        timeline_before = self._timeline_read.get_by_creative_id(session, training.creative_id)
        before_by_idx: dict[int, TimelineScene] = {}
        if timeline_before:
            before_by_idx = {s.scene_index: s for s in timeline_before.timeline_scenes}

        existing = {a.scene_index: a for a in self._adjustments.list_by_session(session, session_id)}

        timeline = self._workspace.submit_timeline(session, session_id, raw_scenes)

        saved: list[EditorialTimelineAdjustment] = []
        for raw in raw_scenes:
            idx = raw.scene_index
            prior = before_by_idx.get(idx)
            prev_adj = existing.get(idx)
            auto_in = prev_adj.auto_detected_start_time if prev_adj else (prior.start_time if prior else raw.start_time)
            auto_out = prev_adj.auto_detected_end_time if prev_adj else (prior.end_time if prior else raw.end_time)
            human_in = round(float(raw.start_time), 3)
            human_out = round(float(raw.end_time), 3)
            delta = round((human_in - auto_in) + (human_out - auto_out), 3)

            if abs(human_in - auto_in) < 1e-3 and abs(human_out - auto_out) < 1e-3:
                continue

            log_timeline_trim(scene=idx, old_in=auto_in, new_in=human_in, old_out=auto_out, new_out=human_out)

            adj = EditorialTimelineAdjustment(
                session_id=session_id,
                scene_index=idx,
                auto_detected_start_time=round(auto_in, 3),
                auto_detected_end_time=round(auto_out, 3),
                human_adjusted_start_time=human_in,
                human_adjusted_end_time=human_out,
                timing_adjustment_delta=delta,
                adjustment_reason=adjustment_reason,
                creative_id=training.creative_id,
                clip_id=raw.clip_id,
            )
            self._adjustments.upsert(session, adj)
            saved.append(adj)

        return timeline, validation, tuple(saved)
