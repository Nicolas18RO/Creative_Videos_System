"""Serialización JSON-safe del informe del motor (aplicación)."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, cast

from aicos.domain.editorial_pattern_engine.entities import EditorialPatternEngineReport


def report_to_jsonable(report: EditorialPatternEngineReport) -> dict[str, Any]:
    return cast(dict[str, Any], asdict(report))


def report_from_jsonable(data: dict[str, Any] | None) -> EditorialPatternEngineReport | None:
    if not data:
        return None
    try:
        from aicos.domain.editorial_dataset.entities import EditorialPattern, HookDetectionResult
        from aicos.domain.editorial_pattern_engine.entities import (
            ClipUsagePressureDigest,
            CutBurstWindow,
            CutRhythmProfile,
            EnrichedSceneFingerprint,
            MomentumFlowProfile,
            NarrativeStructureSketch,
            PerClipUsagePressure,
        )

        def _efp(d: dict[str, Any]) -> EnrichedSceneFingerprint:
            return EnrichedSceneFingerprint(
                scene_index=int(d["scene_index"]),
                clip_id=str(d["clip_id"]),
                editorial_label=str(d["editorial_label"]),
                start_time=float(d["start_time"]),
                end_time=float(d["end_time"]),
                duration_sec=float(d["duration_sec"]),
                transition_type=str(d["transition_type"]),
                motion_intensity=float(d["motion_intensity"]),
                visual_energy=float(d["visual_energy"]),
                camera_type=str(d["camera_type"]),
                semantic_tags=tuple(str(x) for x in d.get("semantic_tags") or ()),
                emotion_tags=tuple(str(x) for x in d.get("emotion_tags") or ()),
                source_video_id=str(d.get("source_video_id") or ""),
                master_reel_id=str(d.get("master_reel_id") or ""),
                production_group=str(d.get("production_group") or ""),
                camera_id_production=str(d.get("camera_id_production") or ""),
                visual_cluster_explicit=str(d.get("visual_cluster_explicit") or ""),
                library_narrative_function=str(d.get("library_narrative_function") or ""),
                library_subcategory=str(d.get("library_subcategory") or ""),
            )

        def _cbw(d: dict[str, Any]) -> CutBurstWindow:
            return CutBurstWindow(
                window_start=float(d["window_start"]),
                window_end=float(d["window_end"]),
                burst_intensity=float(d["burst_intensity"]),
                shots_in_window=int(d["shots_in_window"]),
            )

        cr = data["cut_rhythm"]
        cut = CutRhythmProfile(
            mean_shot_duration=float(cr["mean_shot_duration"]),
            std_shot_duration=float(cr["std_shot_duration"]),
            coefficient_of_variation=float(cr["coefficient_of_variation"]),
            cuts_per_minute=float(cr["cuts_per_minute"]),
            acceleration_index=float(cr["acceleration_index"]),
            burst_windows=tuple(_cbw(cast(dict[str, Any], x)) for x in cr.get("burst_windows") or ()),
        )
        mom = data["momentum"]
        momentum = MomentumFlowProfile(
            momentum_samples=tuple(float(x) for x in mom.get("momentum_samples") or ()),
            mean_momentum=float(mom["mean_momentum"]),
            momentum_variance=float(mom["momentum_variance"]),
            reversal_count=int(mom["reversal_count"]),
            sustained_high_blocks=int(mom["sustained_high_blocks"]),
        )
        nar = data["narrative_sketch"]
        narrative = NarrativeStructureSketch(
            phase_labels=tuple(str(x) for x in nar.get("phase_labels") or ()),
            phase_confidence=float(nar["phase_confidence"]),
            dominant_structure_name=str(nar["dominant_structure_name"]),
        )
        ud = data["usage_digest"]
        by_clip = tuple(
            PerClipUsagePressure(
                clip_id=str(x["clip_id"]),
                global_selection_count=int(x["global_selection_count"]),
                distinct_sessions=int(x["distinct_sessions"]),
                mean_final_score=float(x["mean_final_score"]),
            )
            for x in ud.get("by_clip") or ()
        )
        usage = ClipUsagePressureDigest(
            by_clip=by_clip,
            timeline_source_entropy=float(ud["timeline_source_entropy"]),
            max_cluster_streak_length=int(ud["max_cluster_streak_length"]),
        )
        hooks = tuple(
            HookDetectionResult(
                window_start=float(h["window_start"]),
                window_end=float(h["window_end"]),
                hook_strength=float(h["hook_strength"]),
                reasons=tuple(str(x) for x in h.get("reasons") or ()),
            )
            for h in data.get("hooks") or ()
        )
        pats = tuple(
            EditorialPattern(
                pattern_id=str(p["pattern_id"]),
                pattern_type=str(p["pattern_type"]),
                pattern_sequence=tuple(str(x) for x in p.get("pattern_sequence") or ()),
                frequency=float(p["frequency"]),
                confidence_score=float(p["confidence_score"]),
            )
            for p in data.get("sequence_patterns") or ()
        )
        enriched = tuple(_efp(cast(dict[str, Any], x)) for x in data.get("enriched_scenes") or ())
        return EditorialPatternEngineReport(
            engine_version=str(data.get("engine_version") or "6.2.0"),
            enriched_scenes=enriched,
            cut_rhythm=cut,
            momentum=momentum,
            narrative_sketch=narrative,
            usage_digest=usage,
            hooks=hooks,
            sequence_patterns=pats,
            editorial_signature_tags=tuple(str(x) for x in data.get("editorial_signature_tags") or ()),
            cinematic_style_overlay=tuple(str(x) for x in data.get("cinematic_style_overlay") or ()),
        )
    except (KeyError, TypeError, ValueError):
        return None
