"""Señales de compatibilidad puras para ranking multi-factor."""

from __future__ import annotations

from aicos.domain.cinematic.entities import ClipSemanticMetadata, EmotionAnalysis
from aicos.domain.cinematic.enums import NarrativeRole


def emotional_compatibility(scene: EmotionAnalysis, clip: ClipSemanticMetadata | None) -> float:
    if clip is None or clip.primary_emotion is None:
        return 0.5
    if clip.primary_emotion == scene.primary_emotion:
        return 1.0
    if clip.primary_emotion in scene.secondary_emotions:
        return 0.82
    return 0.35


def narrative_compatibility(scene_role: NarrativeRole, clip: ClipSemanticMetadata | None) -> float:
    if clip is None or not clip.narrative_roles:
        return 0.5
    if scene_role in clip.narrative_roles:
        return 1.0
    if scene_role == NarrativeRole.UNKNOWN:
        return 0.55
    return 0.38


def pacing_compatibility(recommended_pacing: str, clip: ClipSemanticMetadata | None) -> float:
    if clip is None or clip.pacing is None:
        return 0.5
    rec = (recommended_pacing or "MEDIUM").upper()
    cp = clip.pacing.value
    if rec == cp:
        return 1.0
    order = ("SLOW", "MEDIUM", "FAST", "VARIED")
    try:
        ri, ci = order.index(rec), order.index(cp)
    except ValueError:
        return 0.5
    return max(0.35, 1.0 - 0.22 * abs(ri - ci))


def cinematic_compatibility(visual_styles: tuple[str, ...], clip: ClipSemanticMetadata | None) -> float:
    if clip is None or not visual_styles:
        return 0.5
    tags = " ".join(clip.semantic_tags).lower() + " " + clip.visual_description.lower()
    hits = sum(1 for vs in visual_styles if vs.replace("_", " ") in tags or vs in tags)
    if hits:
        return min(1.0, 0.5 + 0.15 * hits)
    return 0.45


def visual_intent_tag_overlap(scene_intent_labels: tuple[str, ...], clip: ClipSemanticMetadata | None) -> float:
    if clip is None or not scene_intent_labels:
        return 0.5
    clip_labels = " ".join(clip.visual_intents).lower()
    hits = sum(1 for lab in scene_intent_labels if lab.lower() in clip_labels)
    if hits:
        return min(1.0, 0.48 + 0.18 * hits)
    return 0.42
