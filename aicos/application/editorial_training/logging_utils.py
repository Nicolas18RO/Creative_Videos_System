"""Logging estructurado para edición de timeline (Fase 6.8)."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def log_timeline_trim(*, scene: int, old_in: float, new_in: float, old_out: float | None = None, new_out: float | None = None) -> None:
    parts = [f"scene={scene}", f"old_in={old_in:.3f}", f"new_in={new_in:.3f}"]
    if old_out is not None and new_out is not None:
        parts.extend([f"old_out={old_out:.3f}", f"new_out={new_out:.3f}"])
    logger.info("[TimelineTrim] %s", " ".join(parts))


def log_merge_preview(*, source: str, duration: float, boundary: float) -> None:
    logger.info("[MergePreview] source=%s duration=%.3f boundary=%.3f", source, duration, boundary)


def log_timeline_validation(*, overlap_detected: bool, issue_count: int, session_id: str = "") -> None:
    logger.info(
        "[TimelineValidation] session=%s overlap_detected=%s issues=%s",
        session_id or "-",
        overlap_detected,
        issue_count,
    )
