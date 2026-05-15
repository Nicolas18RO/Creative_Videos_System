"""Firmas editoriales a partir de huellas enriquecidas (dominio puro)."""

from __future__ import annotations

from aicos.domain.editorial_pattern_engine.entities import EnrichedSceneFingerprint


def derive_editorial_signature_tags(
    scenes: tuple[EnrichedSceneFingerprint, ...],
) -> tuple[str, ...]:
    tags: set[str] = set()
    if len(scenes) < 2:
        return ()
    sources = [s.source_video_id for s in scenes if s.source_video_id]
    if len(sources) >= 2:
        alts = sum(1 for i in range(1, len(sources)) if sources[i] != sources[i - 1])
        if alts >= len(sources) * 0.45:
            tags.add("alternating_sources")
        if alts <= len(sources) * 0.2 and len(set(sources)) <= 2:
            tags.add("source_cohesion")

    clusters = [s.visual_cluster_explicit for s in scenes if s.visual_cluster_explicit]
    run = 1
    max_run = 1
    for i in range(1, len(clusters)):
        if clusters[i] == clusters[i - 1]:
            run += 1
            max_run = max(max_run, run)
        else:
            run = 1
    if max_run >= 3:
        tags.add(f"cluster_streak_{max_run}")

    durs = [s.duration_sec for s in scenes]
    if durs:
        mean_d = sum(durs) / len(durs)
        short_ratio = sum(1 for d in durs if d < mean_d * 0.55) / len(durs)
        if short_ratio > 0.35:
            tags.add("staccato_editing")

    trans = [s.transition_type.lower() for s in scenes]
    if sum(1 for t in trans if t not in ("", "cut", "none", "hard_cut")) >= max(2, len(trans) // 4):
        tags.add("transition_forwarding")

    return tuple(sorted(tags))


def derive_cinematic_style_overlay(scenes: tuple[EnrichedSceneFingerprint, ...]) -> tuple[str, ...]:
    out: set[str] = set()
    for s in scenes:
        ct = s.camera_type.lower()
        if "macro" in ct or "macro" in s.library_subcategory.lower():
            out.add("macro_language")
        if s.camera_id_production:
            out.add("production_camera_aware")
        if s.production_group:
            out.add("production_grouped")
    return tuple(sorted(out))
