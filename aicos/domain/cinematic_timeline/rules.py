"""Mutaciones puras del timeline de proyecto."""

from __future__ import annotations

import uuid
from dataclasses import replace

from aicos.domain.cinematic_timeline.entities import ProjectTimelineScene

MIN_SCENE_MS = 50
_ROLE_PRIORITY = ("HOOK", "PROBLEM", "BENEFIT", "RESULT", "AUTHORITY", "SOCIAL_PROOF", "PRODUCT", "CTA", "NATURAL")


def _pick_narrative(a: str, b: str) -> str:
    ra = (a or "NATURAL").strip().upper()
    rb = (b or "NATURAL").strip().upper()
    for role in _ROLE_PRIORITY:
        if ra == role or rb == role:
            return role
    return ra or rb or "NATURAL"


def _reindex_chronological(scenes: list[ProjectTimelineScene]) -> list[ProjectTimelineScene]:
    ordered = sorted(scenes, key=lambda s: (s.start_ms, s.scene_index))
    return [replace(s, scene_index=i) for i, s in enumerate(ordered)]


def _reindex_sequential(scenes: list[ProjectTimelineScene]) -> list[ProjectTimelineScene]:
    """Conserva el orden de la lista (p. ej. drag reorder) y solo renumera índices."""
    return [replace(s, scene_index=i) for i, s in enumerate(scenes)]


def validate_project_timeline(
    scenes: tuple[ProjectTimelineScene, ...],
    *,
    timeline_duration_ms: int | None = None,
) -> tuple[bool, str]:
    if not scenes:
        return True, ""
    ordered = sorted(scenes, key=lambda s: s.scene_index)
    for s in ordered:
        if s.end_ms <= s.start_ms:
            return False, f"scene {s.scene_index}: end must be after start"
        if s.duration_ms < MIN_SCENE_MS:
            return False, f"scene {s.scene_index}: duration too short"
    for i in range(len(ordered) - 1):
        if ordered[i].end_ms > ordered[i + 1].start_ms + 1:
            return False, f"overlap between scene {ordered[i].scene_index} and {ordered[i + 1].scene_index}"
    if timeline_duration_ms is not None:
        if ordered[-1].end_ms > timeline_duration_ms + 1:
            return False, "timeline exceeds project duration"
    return True, ""


def merge_project_scenes(
    left: ProjectTimelineScene,
    right: ProjectTimelineScene,
) -> ProjectTimelineScene:
    """Fusiona dos escenas adyacentes en una (conserva scene_id izquierda)."""
    start = min(left.start_ms, right.start_ms)
    end = max(left.end_ms, right.end_ms)
    text = f"{left.text.strip()}\n{right.text.strip()}".strip()
    concept = left.concept if len(left.concept) >= len(right.concept) else right.concept
    clip = left.selected_clip_id or right.selected_clip_id
    return replace(
        left,
        start_ms=start,
        end_ms=end,
        duration_ms=end - start,
        text=text or left.text,
        concept=concept or left.concept,
        narrative_function=_pick_narrative(left.narrative_function, right.narrative_function),
        is_hook=left.is_hook or right.is_hook,
        selected_clip_id=clip,
    )


def split_project_scene(
    scene: ProjectTimelineScene,
    split_at_ms: int,
) -> tuple[ProjectTimelineScene, ProjectTimelineScene]:
    """Divide una escena en dos por tiempo (texto repartido por proporción)."""
    if split_at_ms <= scene.start_ms or split_at_ms >= scene.end_ms:
        raise ValueError("split_point_out_of_bounds")
    ratio = (split_at_ms - scene.start_ms) / max(1, scene.duration_ms)
    words = scene.text.split()
    cut = max(1, min(len(words) - 1, int(len(words) * ratio))) if len(words) > 1 else 0
    left_text = " ".join(words[:cut]) if cut else scene.text[: max(1, len(scene.text) // 2)]
    right_text = " ".join(words[cut:]) if cut else scene.text[len(left_text) :].strip() or scene.text
    left = replace(
        scene,
        end_ms=split_at_ms,
        duration_ms=split_at_ms - scene.start_ms,
        text=left_text.strip() or scene.text,
    )
    right = replace(
        scene,
        scene_id=str(uuid.uuid4()),
        scene_index=scene.scene_index + 1,
        start_ms=split_at_ms,
        end_ms=scene.end_ms,
        duration_ms=scene.end_ms - split_at_ms,
        text=right_text.strip() or scene.text,
        selected_clip_id=None,
    )
    return left, right


def trim_project_scene(
    scene: ProjectTimelineScene,
    *,
    start_ms: int,
    end_ms: int,
) -> ProjectTimelineScene:
    if end_ms <= start_ms:
        raise ValueError("invalid_trim_range")
    if start_ms < scene.start_ms or end_ms > scene.end_ms:
        raise ValueError("trim_outside_scene_bounds")
    return replace(
        scene,
        start_ms=start_ms,
        end_ms=end_ms,
        duration_ms=end_ms - start_ms,
    )


def reorder_scenes(
    scenes: list[ProjectTimelineScene],
    from_index: int,
    to_index: int,
) -> list[ProjectTimelineScene]:
    """Reordena por scene_index visual (drag); reindexa 0..n-1 sin reordenar por tiempo."""
    if from_index == to_index:
        return _reindex_sequential(sorted(scenes, key=lambda s: s.scene_index))
    ordered = sorted(scenes, key=lambda s: s.scene_index)
    if from_index < 0 or to_index < 0 or from_index >= len(ordered) or to_index >= len(ordered):
        raise ValueError("invalid_reorder_index")
    moving = ordered.pop(from_index)
    ordered.insert(to_index, moving)
    return _reindex_sequential(ordered)
