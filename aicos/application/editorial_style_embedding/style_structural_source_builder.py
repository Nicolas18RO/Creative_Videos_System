"""Construye señales agregadas para el encoder estructural (aplicación)."""

from __future__ import annotations

import statistics
from typing import Any

from aicos.domain.editorial_dataset.entities import CreativeTimeline
from aicos.domain.editorial_pattern_engine.cut_rhythm import analyze_cut_rhythm
from aicos.domain.editorial_pattern_engine.momentum_flow import compute_momentum_flow
from aicos.domain.editorial_pattern_engine.narrative_arc import infer_narrative_structure
from aicos.domain.editorial_style_embedding.digest_builder import summarize_patterns_for_digest
from aicos.domain.editorial_style_embedding.entities import StyleStructuralSource


def _narrative_bucket(name: str) -> int:
    n = (name or "").lower()
    if "classic" in n:
        return 1
    if "modular" in n:
        return 2
    if "undetected" in n or not n:
        return 0
    return 3


def build_style_structural_source(timeline: CreativeTimeline, report: Any | None) -> StyleStructuralSource:
    scenes = timeline.timeline_scenes
    sp = timeline.style_profile
    ss = timeline.style_signals
    duration = max((s.end_time for s in scenes), default=0.0)
    curve = ss.emotional_curve
    em_mean = float(statistics.fmean(curve)) if curve else 0.5
    em_std = float(statistics.pstdev(curve)) if len(curve) > 1 else 0.0

    starts = tuple(s.start_time for s in scenes)
    durs = tuple(s.duration for s in scenes)
    cut = analyze_cut_rhythm(starts, durs) if scenes else analyze_cut_rhythm((), ())
    mom = compute_momentum_flow(
        tuple(s.motion_intensity for s in scenes),
        tuple(s.visual_energy for s in scenes),
    )
    nar = infer_narrative_structure(
        tuple(s.narrative_role for s in scenes),
        tuple(s.visual_energy for s in scenes),
    )

    sig_tags: tuple[str, ...] = ()
    overlay: tuple[str, ...] = ()
    patterns_summary: tuple[str, ...] = ()
    src_entropy = 0.0
    streak_n = 0.0
    pressure_mean = 0.0

    if report is not None:
        cut = report.cut_rhythm
        mom = report.momentum
        nar = report.narrative_sketch
        sig_tags = tuple(report.editorial_signature_tags)
        overlay = tuple(report.cinematic_style_overlay)
        patterns_summary = summarize_patterns_for_digest(report.sequence_patterns)
        ud = report.usage_digest
        src_entropy = float(ud.timeline_source_entropy)
        streak_n = min(1.0, float(ud.max_cluster_streak_length) / 8.0)
        if ud.by_clip:
            pressure_mean = float(
                statistics.fmean(max(0.0, min(1.0, p.global_selection_count / 25.0)) for p in ud.by_clip)
            )

    rev_norm = min(1.0, float(mom.reversal_count) / max(len(scenes), 1))
    high_norm = min(1.0, float(mom.sustained_high_blocks) / max(len(scenes) // 2, 1))

    top_tokens: list[str] = []
    for line in patterns_summary:
        parts = line.replace(":", " ").replace("@", " ").split()
        top_tokens.extend(parts[:8])
    top_tuple = tuple(dict.fromkeys(top_tokens))[:24]

    return StyleStructuralSource(
        creative_id=timeline.creative_id,
        scene_count=len(scenes),
        total_duration_sec=float(duration),
        hook_intensity=float(sp.hook_intensity),
        average_pacing=float(sp.average_pacing),
        motion_density=float(sp.motion_density),
        transition_density=float(sp.transition_density),
        narrative_aggressiveness=float(sp.narrative_aggressiveness),
        visual_dynamism=float(sp.visual_dynamism),
        pacing_score=float(ss.pacing_score),
        hook_strength_signal=float(ss.hook_strength),
        emotional_curve_mean=em_mean,
        emotional_curve_std=em_std,
        cut_mean_shot_sec=float(cut.mean_shot_duration),
        cut_std_shot_sec=float(cut.std_shot_duration),
        cut_cv=float(cut.coefficient_of_variation),
        cuts_per_minute=float(cut.cuts_per_minute),
        cut_accel=float(cut.acceleration_index),
        burst_window_count=len(cut.burst_windows),
        momentum_mean=float(mom.mean_momentum),
        momentum_variance=float(mom.momentum_variance),
        momentum_reversals_norm=rev_norm,
        sustained_high_blocks_norm=high_norm,
        narrative_phase_confidence=float(nar.phase_confidence),
        narrative_structure_bucket=_narrative_bucket(nar.dominant_structure_name),
        usage_source_entropy=src_entropy,
        usage_max_cluster_streak_norm=streak_n,
        usage_pressure_mean_norm=pressure_mean,
        signature_tags=sig_tags,
        cinematic_overlay_tags=overlay,
        top_pattern_tokens=top_tuple,
    )
