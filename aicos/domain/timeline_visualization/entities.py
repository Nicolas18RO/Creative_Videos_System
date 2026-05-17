"""Entidades puras del timeline visual cinematográfico."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TimelineClipPreview:
    """Vista previa de un clip/escena en la línea de tiempo."""

    clip_id: str
    scene_index: int
    thumbnail_path: str
    preview_video_path: str
    start_time: float
    end_time: float
    duration: float
    motion_score: float
    narrative_role: str
    visual_cluster_id: str
    timeline_position: float


@dataclass(frozen=True, slots=True)
class TimelineVisualTrack:
    """Pista visual agregada de un creativo."""

    creative_id: str
    timeline_duration: float
    clip_previews: tuple[TimelineClipPreview, ...]
    pacing_density: tuple[float, ...]
    transition_density: tuple[float, ...]
    motion_curve: tuple[float, ...]


@dataclass(frozen=True, slots=True)
class ClipVisualInspection:
    """Señales de inspección rápida para revisión editorial."""

    clip_id: str
    scene_index: int
    motion_intensity: float
    visual_similarity: float
    cut_speed: float
    transition_type: str
    frame_density: float
    hook_probability: float
