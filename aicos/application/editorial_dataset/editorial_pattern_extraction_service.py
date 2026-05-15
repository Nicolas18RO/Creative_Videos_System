"""Detección de patrones editoriales — delega en motor Fase 6.2 y señales 6.1."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from aicos.application.editorial_dataset import logging_utils
from aicos.config import EditorialDatasetConfig, EditorialPatternEngineConfig
from aicos.domain.editorial_dataset.entities import (
    CreativeTimeline,
    EditorialPattern,
    HookDetectionResult,
    TimelineScene,
)
from aicos.domain.editorial_dataset.rules import scene_editorial_label
from aicos.domain.editorial_dataset.signals import build_style_profile_and_signals
from aicos.domain.editorial_pattern_engine.opening_hook_signal import detect_opening_hook
from aicos.domain.editorial_pattern_engine.sequence_mining import mine_recurrent_sequences
from aicos.services.editorial_pattern_engine_factory import build_editorial_pattern_extraction_engine


class EditorialPatternExtractionService:
    """Orquesta el ``EditorialPatternExtractionEngine`` (6.2) y el perfil agregado (6.1)."""

    def __init__(
        self,
        dataset_cfg: EditorialDatasetConfig,
        engine_cfg: EditorialPatternEngineConfig,
    ) -> None:
        self._ds = dataset_cfg
        self._eng_cfg = engine_cfg

    def attach_patterns_to_timeline(
        self,
        timeline: CreativeTimeline,
        session: Any | None = None,
    ) -> CreativeTimeline:
        engine = build_editorial_pattern_extraction_engine(session)
        report = engine.build_report(timeline, session)

        hooks = report.hooks if self._ds.detect_hooks else ()
        patterns = report.sequence_patterns if self._ds.detect_patterns else ()
        hook_strength = float(hooks[0].hook_strength) if hooks else 0.0

        merged_tags = tuple(
            sorted(set(report.cinematic_style_overlay).union(set(report.editorial_signature_tags)))
        )
        profile, signals = build_style_profile_and_signals(
            timeline.timeline_scenes,
            hook_strength=hook_strength,
            cinematic_style_tags=merged_tags,
        )
        logging_utils.log_style_profile(
            "creative=%s engine=%s patterns=%s",
            timeline.creative_id,
            report.engine_version,
            len(patterns),
        )
        return replace(
            timeline,
            editorial_patterns=patterns,
            hook_detection=hooks,
            style_profile=profile,
            style_signals=signals,
            pattern_engine_report=report,
        )

    def detect_hooks(self, scenes: tuple[TimelineScene, ...]) -> tuple[HookDetectionResult, ...]:
        if not self._ds.detect_hooks or not scenes:
            return ()
        return detect_opening_hook(
            scenes,
            min_hook_duration=self._ds.min_hook_duration,
            max_hook_duration=self._ds.max_hook_duration,
        )

    def extract_editorial_patterns(
        self, scenes: tuple[TimelineScene, ...]
    ) -> tuple[EditorialPattern, ...]:
        if not self._ds.detect_patterns or len(scenes) < 2:
            return ()
        labels = tuple(scene_editorial_label(s) for s in scenes)
        return mine_recurrent_sequences(labels)
