"""Validación y normalización pura de timelines editoriales."""

from __future__ import annotations

import re

from aicos.domain.editorial_dataset.entities import TimelineScene

_TAG_SPLIT = re.compile(r"[,;|]+")


def normalize_tag_list(raw: str | None) -> tuple[str, ...]:
    if not raw or not str(raw).strip():
        return ()
    parts = _TAG_SPLIT.split(str(raw).strip().lower())
    seen: set[str] = set()
    out: list[str] = []
    for p in parts:
        t = p.strip()
        if not t or t in seen:
            continue
        seen.add(t)
        out.append(t)
    return tuple(out)


def validate_timeline_scenes(scenes: tuple[TimelineScene, ...]) -> tuple[bool, str]:
    if not scenes:
        return False, "timeline_vacio"
    prev_idx = -1
    prev_end = -1.0
    for s in scenes:
        if s.scene_index != prev_idx + 1:
            return False, f"scene_index_no_secuencial:esperado_{prev_idx + 1}_recibido_{s.scene_index}"
        prev_idx = s.scene_index
        if s.end_time < s.start_time:
            return False, "end_time_menor_que_start_time"
        if s.duration < 0:
            return False, "duration_negativa"
        if abs(s.duration - (s.end_time - s.start_time)) > 1e-3:
            return False, "duration_inconsistente_con_rango"
        if s.start_time < prev_end - 1e-6:
            return False, "solapamiento_temporal"
        prev_end = max(prev_end, s.end_time)
    return True, ""


def scene_editorial_label(scene: TimelineScene) -> str:
    """Etiqueta de secuencia editorial (roles + semántica), no solo clip_id."""
    nr = (scene.narrative_role or "").strip().lower().replace(" ", "_")
    if nr:
        base = nr
    elif scene.semantic_tags:
        base = scene.semantic_tags[0]
    else:
        base = "cut"
    return base[:128]
