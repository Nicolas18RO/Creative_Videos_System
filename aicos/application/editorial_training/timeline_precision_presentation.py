"""DTOs de presentación para edición precisa (Fase 6.8)."""

from __future__ import annotations

from aicos.domain.editorial_training.entities import EditorialTimelineAdjustment
from aicos.domain.editorial_training.merge_preview import MergePreviewResult
from aicos.domain.editorial_training.timeline_rules import TimelineValidationResult
from aicos.models.schemas import (
    EditorialTimelineAdjustmentOut,
    MergePreviewSceneSliceOut,
    MergePreviewResultOut,
    TimelineValidationIssueOut,
    TimelineValidationResultOut,
)


def merge_preview_to_out(preview: MergePreviewResult) -> MergePreviewResultOut:
    def _slice(s) -> MergePreviewSceneSliceOut:
        return MergePreviewSceneSliceOut(
            scene_index=s.scene_index,
            start_time=s.start_time,
            end_time=s.end_time,
            duration=s.duration,
            clip_id=s.clip_id,
            narrative_role=s.narrative_role,
        )

    return MergePreviewResultOut(
        scene_a=_slice(preview.scene_a),
        scene_b=_slice(preview.scene_b),
        merged=_slice(preview.merged),
        removed_boundary_time=preview.removed_boundary_time,
        total_duration=preview.total_duration,
    )


def validation_to_out(result: TimelineValidationResult) -> TimelineValidationResultOut:
    return TimelineValidationResultOut(
        valid=result.valid,
        issues=[
            TimelineValidationIssueOut(
                code=i.code,
                message=i.message,
                scene_index=i.scene_index,
                related_scene_index=i.related_scene_index,
            )
            for i in result.issues
        ],
        normalized=[
            {"scene_index": s.scene_index, "start_time": s.start_time, "end_time": s.end_time}
            for s in result.normalized
        ],
    )


def adjustment_to_out(adj: EditorialTimelineAdjustment) -> EditorialTimelineAdjustmentOut:
    return EditorialTimelineAdjustmentOut(
        session_id=adj.session_id,
        scene_index=adj.scene_index,
        clip_id=adj.clip_id,
        auto_detected_start_time=adj.auto_detected_start_time,
        auto_detected_end_time=adj.auto_detected_end_time,
        human_adjusted_start_time=adj.human_adjusted_start_time,
        human_adjusted_end_time=adj.human_adjusted_end_time,
        timing_adjustment_delta=adj.timing_adjustment_delta,
        adjustment_reason=adj.adjustment_reason,
    )
