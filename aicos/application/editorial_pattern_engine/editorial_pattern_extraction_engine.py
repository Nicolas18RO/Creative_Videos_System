"""Motor de extracción de patrones editoriales (Fase 6.2) — orquestación timeline-aware."""

from __future__ import annotations

from dataclasses import replace

from aicos.application.editorial_pattern_engine import logging_utils
from aicos.application.editorial_pattern_engine.ports import (
    ClipUsageHistoryDigestPort,
    TimelinePatternEnrichmentPort,
)
from aicos.config import EditorialDatasetConfig, EditorialPatternEngineConfig
from aicos.domain.editorial_dataset.entities import CreativeTimeline, EditorialPattern
from aicos.domain.editorial_dataset.rules import scene_editorial_label
from aicos.domain.editorial_pattern_engine.cut_rhythm import analyze_cut_rhythm
from aicos.domain.editorial_pattern_engine.editorial_signatures import (
    derive_cinematic_style_overlay,
    derive_editorial_signature_tags,
)
from aicos.domain.editorial_pattern_engine.entities import (
    ClipUsagePressureDigest,
    EditorialPatternEngineReport,
    EnrichedSceneFingerprint,
    TimelineEnrichmentBundle,
    merge_scene_with_enrichment,
)
from aicos.domain.editorial_pattern_engine.momentum_flow import compute_momentum_flow
from aicos.domain.editorial_pattern_engine.narrative_arc import infer_narrative_structure
from aicos.domain.editorial_pattern_engine.opening_hook_signal import detect_opening_hook
from aicos.domain.editorial_pattern_engine.sequence_mining import (
    mine_production_aware_sequences,
    mine_recurrent_sequences,
)
from aicos.domain.editorial_pattern_engine.usage_cohesion import (
    max_cluster_streak,
    timeline_source_entropy,
)


class EditorialPatternExtractionEngine:
    """Integra Fase 4 (uso), Fase 5 (cinemática) y señales de timeline (6.1)."""

    def __init__(
        self,
        *,
        dataset_cfg: EditorialDatasetConfig,
        engine_cfg: EditorialPatternEngineConfig,
        enrichment: TimelinePatternEnrichmentPort | None,
        usage_digest: ClipUsageHistoryDigestPort | None,
    ) -> None:
        self._ds = dataset_cfg
        self._eng = engine_cfg
        self._enrichment = enrichment
        self._usage = usage_digest

    def build_report(self, timeline: CreativeTimeline, session: Any | None) -> EditorialPatternEngineReport:
        if not self._eng.enabled:
            return self._minimal_report(timeline)

        scenes = timeline.timeline_scenes
        clip_ids = [s.clip_id for s in scenes if s.clip_id]

        bundle = TimelineEnrichmentBundle(cinematic_by_clip={}, library_by_clip={})
        if session is not None and self._enrichment is not None:
            if self._eng.use_cinematic_enrichment or self._eng.use_library_taxonomy:
                bundle = self._enrichment.load_bundle(session, clip_ids)

        digest = ClipUsagePressureDigest(
            by_clip=tuple(),
            timeline_source_entropy=0.0,
            max_cluster_streak_length=0,
        )
        if session is not None and self._usage is not None and self._eng.use_clip_usage_history:
            digest = self._usage.build_digest(session, clip_ids)

        enriched: list[EnrichedSceneFingerprint] = []
        labels: list[str] = []
        prod_labels: list[str] = []
        for s in scenes:
            lab = scene_editorial_label(s)
            labels.append(lab)
            cine = bundle.cinematic_by_clip.get(s.clip_id) if bundle.cinematic_by_clip else None
            lib = bundle.library_by_clip.get(s.clip_id) if bundle.library_by_clip else None
            if not self._eng.use_cinematic_enrichment:
                cine = None
            if not self._eng.use_library_taxonomy:
                lib = None
            ef = merge_scene_with_enrichment(s, editorial_label=lab, cine=cine, lib=lib)
            enriched.append(ef)
            src = (ef.source_video_id or "na")[:10]
            prod_labels.append(f"{lab}@{src}")

        enriched_t = tuple(enriched)
        starts = tuple(s.start_time for s in scenes)
        durs = tuple(s.duration for s in scenes)
        cut = analyze_cut_rhythm(starts, durs) if scenes else analyze_cut_rhythm((), ())
        if scenes and not self._eng.detect_cut_bursts:
            cut = replace(cut, burst_windows=())

        mom = compute_momentum_flow(
            tuple(s.motion_intensity for s in scenes),
            tuple(s.visual_energy for s in scenes),
        )
        if scenes and not self._eng.detect_momentum_reversals:
            mom = replace(mom, reversal_count=0)

        narrative = infer_narrative_structure(
            tuple(s.narrative_role for s in scenes),
            tuple(s.visual_energy for s in scenes),
        )
        if scenes and not self._eng.narrative_arc_detection:
            narrative = replace(
                narrative,
                phase_labels=tuple(),
                phase_confidence=0.0,
                dominant_structure_name="undetected",
            )

        hooks = ()
        if self._ds.detect_hooks:
            hooks = detect_opening_hook(
                scenes,
                min_hook_duration=self._ds.min_hook_duration,
                max_hook_duration=self._ds.max_hook_duration,
            )

        seq_patterns: list[EditorialPattern] = []
        if self._ds.detect_patterns and len(scenes) >= 2:
            seq_patterns.extend(mine_recurrent_sequences(tuple(labels)))
            seq_patterns.extend(mine_production_aware_sequences(tuple(prod_labels)))
        # Dedupe por pattern_id
        seen: set[str] = set()
        uniq: list[EditorialPattern] = []
        for p in sorted(seq_patterns, key=lambda x: (-x.frequency, -x.confidence_score)):
            if p.pattern_id in seen:
                continue
            seen.add(p.pattern_id)
            uniq.append(p)

        src_entropy = timeline_source_entropy(tuple(e.source_video_id for e in enriched_t))
        streak = max_cluster_streak(tuple(e.visual_cluster_explicit for e in enriched_t))
        digest = ClipUsagePressureDigest(
            by_clip=digest.by_clip,
            timeline_source_entropy=float(src_entropy),
            max_cluster_streak_length=int(max(digest.max_cluster_streak_length, streak)),
        )

        sig_tags = derive_editorial_signature_tags(enriched_t)
        cin_overlay = derive_cinematic_style_overlay(enriched_t)

        report = EditorialPatternEngineReport(
            engine_version="6.2.0",
            enriched_scenes=enriched_t,
            cut_rhythm=cut,
            momentum=mom,
            narrative_sketch=narrative,
            usage_digest=digest,
            hooks=hooks,
            sequence_patterns=tuple(uniq),
            editorial_signature_tags=sig_tags,
            cinematic_style_overlay=cin_overlay,
        )
        logging_utils.log_pattern_engine(
            "creative=%s enriched=%s patterns=%s hooks=%s",
            timeline.creative_id,
            len(enriched_t),
            len(report.sequence_patterns),
            len(report.hooks),
        )
        return report

    def _minimal_report(self, timeline: CreativeTimeline) -> EditorialPatternEngineReport:
        scenes = timeline.timeline_scenes
        enriched = tuple(
            merge_scene_with_enrichment(
                s,
                editorial_label=scene_editorial_label(s),
                cine=None,
                lib=None,
            )
            for s in scenes
        )
        starts = tuple(s.start_time for s in scenes)
        durs = tuple(s.duration for s in scenes)
        cut = analyze_cut_rhythm(starts, durs) if scenes else analyze_cut_rhythm((), ())
        mom = compute_momentum_flow(
            tuple(s.motion_intensity for s in scenes),
            tuple(s.visual_energy for s in scenes),
        )
        narrative = infer_narrative_structure(
            tuple(s.narrative_role for s in scenes),
            tuple(s.visual_energy for s in scenes),
        )
        return EditorialPatternEngineReport(
            engine_version="6.2.0-off",
            enriched_scenes=enriched,
            cut_rhythm=cut,
            momentum=mom,
            narrative_sketch=narrative,
            usage_digest=ClipUsagePressureDigest(
                by_clip=tuple(), timeline_source_entropy=0.0, max_cluster_streak_length=0
            ),
            hooks=(),
            sequence_patterns=tuple(),
            editorial_signature_tags=derive_editorial_signature_tags(enriched)
            if enriched
            else tuple(),
            cinematic_style_overlay=derive_cinematic_style_overlay(enriched)
            if enriched
            else tuple(),
        )
