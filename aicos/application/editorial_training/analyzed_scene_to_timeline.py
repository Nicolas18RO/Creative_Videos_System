"""Mapeo de salida del analizador de audio a escenas crudas del timeline editorial."""

from __future__ import annotations

from collections.abc import Sequence

from aicos.application.editorial_dataset.ports import RawTimelineSceneInput
from aicos.domain.editorial_dataset.rules import normalize_tag_list
from aicos.models.schemas import AnalyzedScene


def map_analyzed_scenes_to_raw_inputs(scenes: Sequence[AnalyzedScene]) -> tuple[RawTimelineSceneInput, ...]:
    """Convierte escenas analizadas (M1–M3) en entradas para ``CreativeTimelineBuilderService``."""
    items: list[RawTimelineSceneInput] = []
    for asc in sorted(scenes, key=lambda x: x.scene.scene_index):
        sc = asc.scene
        clip_id = asc.recommendations[0].clip_id if asc.recommendations else f"unassigned_{sc.scene_index}"
        start = sc.start_ms / 1000.0
        end = sc.end_ms / 1000.0
        hook = float(sc.hook_score or 0.0)
        motion = max(0.0, min(1.0, 0.25 + (1.0 if sc.is_hook else 0.0) * 0.35 + min(hook, 1.0) * 0.4))
        visual = max(0.0, min(1.0, 0.2 + (1.0 if sc.is_hook else 0.0) * 0.5 + min(hook, 1.0) * 0.45))
        sem = normalize_tag_list(sc.concept) if (sc.concept or "").strip() else ()
        nr = (sc.narrative_function or "NATURAL").strip() or "NATURAL"
        items.append(
            RawTimelineSceneInput(
                scene_index=int(sc.scene_index),
                clip_id=str(clip_id)[:128],
                start_time=float(start),
                end_time=float(end),
                transition_type="cut",
                narrative_role=nr,
                motion_intensity=motion,
                visual_energy=visual,
                camera_type="",
                semantic_tags=sem,
                emotion_tags=(),
            )
        )
    return tuple(items)
