"""Entidades puras del timeline de proyecto (no ORM)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProjectTimelineScene:
    scene_id: str
    scene_index: int
    start_ms: int
    end_ms: int
    duration_ms: int
    text: str
    concept: str
    narrative_function: str
    is_hook: bool
    gender_hint: str | None
    selected_clip_id: str | None

    @property
    def start_sec(self) -> float:
        return self.start_ms / 1000.0

    @property
    def end_sec(self) -> float:
        return self.end_ms / 1000.0
