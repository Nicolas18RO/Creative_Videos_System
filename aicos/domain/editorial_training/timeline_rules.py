"""Reglas puras de validación de límites de escenas (Fase 6.8)."""

from __future__ import annotations

from dataclasses import dataclass

DEFAULT_MIN_SCENE_DURATION_SEC = 0.05
DEFAULT_MAX_SCENE_DURATION_SEC = 600.0
DEFAULT_MAX_GAP_SEC = 0.5


@dataclass(frozen=True, slots=True)
class SceneBoundary:
    scene_index: int
    start_time: float
    end_time: float


@dataclass(frozen=True, slots=True)
class TimelineValidationIssue:
    code: str
    message: str
    scene_index: int | None = None
    related_scene_index: int | None = None


@dataclass(frozen=True, slots=True)
class TimelineValidationResult:
    valid: bool
    issues: tuple[TimelineValidationIssue, ...]
    normalized: tuple[SceneBoundary, ...]


def _round3(value: float) -> float:
    return round(float(value), 3)


def normalize_scene_boundaries(
    scenes: tuple[SceneBoundary, ...],
    *,
    timeline_duration: float | None = None,
) -> tuple[SceneBoundary, ...]:
    """Ordena por índice y recorta OUT al máximo de timeline si se conoce."""
    ordered = tuple(sorted(scenes, key=lambda s: s.scene_index))
    if timeline_duration is None:
        return tuple(
            SceneBoundary(
                scene_index=s.scene_index,
                start_time=_round3(s.start_time),
                end_time=_round3(max(s.end_time, s.start_time)),
            )
            for s in ordered
        )
    cap = float(timeline_duration)
    out: list[SceneBoundary] = []
    for s in ordered:
        start = _round3(max(0.0, min(s.start_time, cap)))
        end = _round3(max(start, min(s.end_time, cap)))
        out.append(SceneBoundary(scene_index=s.scene_index, start_time=start, end_time=end))
    return tuple(out)


def validate_scene_boundaries(
    scenes: tuple[SceneBoundary, ...],
    *,
    timeline_duration: float | None = None,
    min_duration: float = DEFAULT_MIN_SCENE_DURATION_SEC,
    max_duration: float = DEFAULT_MAX_SCENE_DURATION_SEC,
    max_gap: float = DEFAULT_MAX_GAP_SEC,
) -> TimelineValidationResult:
    """Valida IN/OUT por escena y coherencia entre escenas adyacentes."""
    issues: list[TimelineValidationIssue] = []
    normalized = normalize_scene_boundaries(scenes, timeline_duration=timeline_duration)

    if not normalized:
        return TimelineValidationResult(valid=True, issues=(), normalized=normalized)

    for s in normalized:
        duration = s.end_time - s.start_time
        if s.end_time <= s.start_time:
            issues.append(
                TimelineValidationIssue(
                    code="invalid_duration",
                    message=f"scene {s.scene_index}: end must be after start",
                    scene_index=s.scene_index,
                )
            )
        elif duration < min_duration:
            issues.append(
                TimelineValidationIssue(
                    code="duration_too_short",
                    message=f"scene {s.scene_index}: duration below minimum",
                    scene_index=s.scene_index,
                )
            )
        elif duration > max_duration:
            issues.append(
                TimelineValidationIssue(
                    code="duration_too_long",
                    message=f"scene {s.scene_index}: duration above maximum",
                    scene_index=s.scene_index,
                )
            )
        if timeline_duration is not None:
            if s.start_time < 0 or s.end_time > timeline_duration + 1e-6:
                issues.append(
                    TimelineValidationIssue(
                        code="out_of_range",
                        message=f"scene {s.scene_index}: outside timeline duration",
                        scene_index=s.scene_index,
                    )
                )

    for i in range(len(normalized) - 1):
        left = normalized[i]
        right = normalized[i + 1]
        if detect_invalid_overlaps(left, right):
            issues.append(
                TimelineValidationIssue(
                    code="overlap",
                    message=(
                        f"scene {left.scene_index} OUT {_round3(left.end_time)} overlaps "
                        f"scene {right.scene_index} IN {_round3(right.start_time)}"
                    ),
                    scene_index=left.scene_index,
                    related_scene_index=right.scene_index,
                )
            )
        gap = right.start_time - left.end_time
        if detect_negative_gaps(gap):
            issues.append(
                TimelineValidationIssue(
                    code="negative_gap",
                    message=(
                        f"scene {right.scene_index} IN before scene {left.scene_index} OUT "
                        f"(gap={_round3(gap)}s)"
                    ),
                    scene_index=right.scene_index,
                    related_scene_index=left.scene_index,
                )
            )
        elif gap > max_gap:
            issues.append(
                TimelineValidationIssue(
                    code="large_gap",
                    message=f"gap of {_round3(gap)}s between scenes {left.scene_index} and {right.scene_index}",
                    scene_index=left.scene_index,
                    related_scene_index=right.scene_index,
                )
            )

    return TimelineValidationResult(
        valid=not issues,
        issues=tuple(issues),
        normalized=normalized,
    )


def detect_invalid_overlaps(left: SceneBoundary, right: SceneBoundary) -> bool:
    return left.end_time > right.start_time + 1e-6


def detect_negative_gaps(gap_seconds: float) -> bool:
    return gap_seconds < -1e-6
