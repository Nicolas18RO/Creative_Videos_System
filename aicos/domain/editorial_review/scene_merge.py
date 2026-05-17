"""Fusión pura de escenas de timeline (sin persistencia)."""

from __future__ import annotations

from aicos.domain.editorial_dataset.entities import TimelineScene
from aicos.domain.editorial_dataset.rules import normalize_tag_list

_ROLE_PRIORITY = ("HOOK", "PROBLEM", "BENEFIT", "RESULT", "AUTHORITY", "SOCIAL_PROOF", "CTA", "NATURAL")


def _pick_narrative_role(a: str, b: str) -> str:
    ra = (a or "NATURAL").strip().upper()
    rb = (b or "NATURAL").strip().upper()
    for role in _ROLE_PRIORITY:
        if ra == role or rb == role:
            return role
    return ra or rb or "NATURAL"


def _merge_tags(a: tuple[str, ...], b: tuple[str, ...]) -> tuple[str, ...]:
    combined = ",".join(list(a) + list(b))
    return normalize_tag_list(combined)


def merge_timeline_scenes(
    left: TimelineScene,
    right: TimelineScene,
    *,
    resulting_scene_index: int,
    resulting_clip_id: str | None = None,
) -> TimelineScene:
    """Crea escena sintética; no muta las originales."""
    start = min(left.start_time, right.start_time)
    end = max(left.end_time, right.end_time)
    duration = max(0.0, end - start)
    clip = resulting_clip_id or left.clip_id or right.clip_id or f"merged_{resulting_scene_index}"
    motion = max(0.0, min(1.0, (left.motion_intensity + right.motion_intensity) / 2.0))
    visual = max(0.0, min(1.0, (left.visual_energy + right.visual_energy) / 2.0))
    transition = left.transition_type if left.start_time <= right.start_time else right.transition_type
    return TimelineScene(
        scene_index=resulting_scene_index,
        clip_id=str(clip)[:128],
        start_time=start,
        end_time=end,
        duration=duration,
        transition_type=transition or "cut",
        narrative_role=_pick_narrative_role(left.narrative_role, right.narrative_role),
        motion_intensity=motion,
        visual_energy=visual,
        camera_type=left.camera_type or right.camera_type,
        semantic_tags=_merge_tags(left.semantic_tags, right.semantic_tags),
        emotion_tags=_merge_tags(left.emotion_tags, right.emotion_tags),
    )


def scene_id_from_index(scene_index: int) -> str:
    return str(int(scene_index))
