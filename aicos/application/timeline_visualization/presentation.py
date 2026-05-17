"""Mapeo dominio → DTOs API (sin lógica FFmpeg)."""

from __future__ import annotations

from urllib.parse import quote

from aicos.domain.timeline_visualization.entities import (
    ClipVisualInspection,
    TimelineClipPreview,
    TimelineVisualTrack,
)
from aicos.models.schemas import (
    ClipVisualInspectionOut,
    TimelineClipPreviewOut,
    TimelineVisualizationResponse,
    TimelineVisualTrackOut,
)


def media_url(creative_id: str, scene_index: int, kind: str) -> str:
    cid = quote(creative_id, safe="")
    return f"/timeline-visualization/media/{cid}/scenes/{scene_index}/{kind}"


def preview_to_out(p: TimelineClipPreview, creative_id: str) -> TimelineClipPreviewOut:
    thumb = media_url(creative_id, p.scene_index, "thumbnail") if p.thumbnail_path else ""
    prev = media_url(creative_id, p.scene_index, "preview") if p.preview_video_path else ""
    return TimelineClipPreviewOut(
        clip_id=p.clip_id,
        scene_index=p.scene_index,
        thumbnail_url=thumb,
        preview_video_url=prev,
        start_time=p.start_time,
        end_time=p.end_time,
        duration=p.duration,
        motion_score=p.motion_score,
        narrative_role=p.narrative_role,
        visual_cluster_id=p.visual_cluster_id,
        timeline_position=p.timeline_position,
    )


def track_to_out(track: TimelineVisualTrack) -> TimelineVisualTrackOut:
    cid = track.creative_id
    return TimelineVisualTrackOut(
        creative_id=cid,
        timeline_duration=track.timeline_duration,
        clip_previews=[preview_to_out(p, cid) for p in track.clip_previews],
        pacing_density=list(track.pacing_density),
        transition_density=list(track.transition_density),
        motion_curve=list(track.motion_curve),
    )


def inspection_to_out(i: ClipVisualInspection) -> ClipVisualInspectionOut:
    return ClipVisualInspectionOut(
        clip_id=i.clip_id,
        scene_index=i.scene_index,
        motion_intensity=i.motion_intensity,
        visual_similarity=i.visual_similarity,
        cut_speed=i.cut_speed,
        transition_type=i.transition_type,
        frame_density=i.frame_density,
        hook_probability=i.hook_probability,
    )


def full_response(track: TimelineVisualTrack) -> TimelineVisualizationResponse:
    return TimelineVisualizationResponse(
        track=track_to_out(track),
        scene_count=len(track.clip_previews),
    )
