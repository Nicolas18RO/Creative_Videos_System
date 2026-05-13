"""Análisis visual local placeholder (OpenCLIP / visión futura vía infraestructura)."""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class StubVisualAnalysisAdapter:
    """Describe frames con heurística trivial hasta conectar modelos locales."""

    def describe_frames(self, frame_paths: list[Path]) -> str:
        logger.info("metadata_generation stage=visual_analysis model=stub frames=%d", len(frame_paths))
        if not frame_paths:
            return ""
        return f"stub_local_vision: sampled {len(frame_paths)} keyframe(s); pending OpenCLIP integration."
