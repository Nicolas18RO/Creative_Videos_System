"""Construcción de DTOs de presentación para el workspace de entrenamiento editorial."""

from __future__ import annotations

from aicos.application.editorial_review.presentation import apply_review_to_scene_card, build_review_lookup
from aicos.application.timeline_visualization.presentation import media_url
from aicos.domain.editorial_dataset.entities import CreativeTimeline, TimelineScene
from aicos.domain.editorial_taxonomy.entities import SceneSemanticIntent
from aicos.domain.editorial_training.entities import EditorialTrainingSession
from aicos.domain.editorial_review.entities import EditorialSceneReviewState
from aicos.domain.editorial_review.scene_merge import scene_id_from_index
from aicos.domain.timeline_visualization.entities import TimelineClipPreview
from aicos.domain.timeline_visualization.pacing import hook_probability_for_scene
from aicos.models.schemas import EditorialTrainingSummaryViewModel, TimelineSceneViewModel


def _energy_label(visual_energy: float) -> str:
    if visual_energy >= 0.66:
        return "high"
    if visual_energy >= 0.33:
        return "medium"
    return "low"


def build_timeline_scene_cards(
    timeline: CreativeTimeline,
    *,
    visual_previews: tuple[TimelineClipPreview, ...] | None = None,
    creative_id: str | None = None,
    review_states: tuple[EditorialSceneReviewState, ...] | None = None,
    semantic_intents: tuple[SceneSemanticIntent, ...] | None = None,
) -> list[TimelineSceneViewModel]:
    cid = creative_id or timeline.creative_id
    by_idx = {p.scene_index: p for p in visual_previews} if visual_previews else {}
    reviews = build_review_lookup(review_states) if review_states else {}
    intents = {o.scene_index: o for o in semantic_intents} if semantic_intents else {}
    out: list[TimelineSceneViewModel] = []
    for s in timeline.timeline_scenes:
        card = _scene_to_card(s, cid, by_idx.get(s.scene_index), intents.get(s.scene_index))
        rev = reviews.get(scene_id_from_index(s.scene_index))
        out.append(apply_review_to_scene_card(card, s, rev))
    return out


def _scene_to_card(
    s: TimelineScene,
    creative_id: str,
    preview: TimelineClipPreview | None,
    semantic: SceneSemanticIntent | None = None,
) -> TimelineSceneViewModel:
    thumb = ""
    prev = ""
    if preview is not None:
        if preview.thumbnail_path:
            thumb = media_url(creative_id, s.scene_index, "thumbnail")
        if preview.preview_video_path:
            prev = media_url(creative_id, s.scene_index, "preview")

    narrative_intent = semantic.effective_narrative_intent if semantic else s.narrative_role
    clip_source = semantic.effective_clip_source if semantic else s.narrative_role

    return TimelineSceneViewModel(
        scene_index=s.scene_index,
        thumbnail_url=thumb,
        preview_video_url=prev,
        hook_score=hook_probability_for_scene(s),
        review_status="pending",
        confidence_score=hook_probability_for_scene(s),
        scene_type_label=semantic.narrative_intent_label if semantic else narrative_intent.replace("_", " ").title(),
        narrative_role=narrative_intent,
        narrative_intent=narrative_intent,
        clip_source_taxonomy=clip_source,
        auto_clip_source_taxonomy=semantic.auto_clip_source_taxonomy if semantic else clip_source,
        human_clip_source_taxonomy=semantic.human_clip_source_taxonomy if semantic else None,
        auto_narrative_intent=semantic.auto_narrative_intent if semantic else narrative_intent,
        human_narrative_intent=semantic.human_narrative_intent if semantic else None,
        emotional_intent=semantic.effective_emotional_intent if semantic else "NEUTRAL",
        auto_emotional_intent=semantic.auto_emotional_intent if semantic else "NEUTRAL",
        human_emotional_intent=semantic.human_emotional_intent if semantic else None,
        audio_fragment_text=semantic.audio_fragment_text if semantic else "",
        visual_style_label=semantic.visual_style_label if semantic else "",
        has_narrative_intent_override=semantic.has_narrative_intent_override if semantic else False,
        has_clip_taxonomy_override=semantic.has_clip_taxonomy_override if semantic else False,
        auto_narrative_role=semantic.auto_narrative_intent if semantic else narrative_intent,
        human_narrative_role=semantic.human_narrative_intent if semantic else None,
        has_category_override=semantic.has_narrative_intent_override if semantic else False,
        time_start=s.start_time,
        time_end=s.end_time,
        duration_seconds=max(0.0, s.end_time - s.start_time),
        energy_label=_energy_label(s.visual_energy),
        motion_intensity=s.motion_intensity,
        visual_energy=s.visual_energy,
        transition_type=s.transition_type,
        semantic_tags=list(s.semantic_tags),
        emotion_tags=list(s.emotion_tags),
        clip_id=s.clip_id,
    )


def build_training_summary(session: EditorialTrainingSession, timeline: CreativeTimeline) -> EditorialTrainingSummaryViewModel:
    hooks = sum(1 for s in timeline.timeline_scenes if (s.narrative_role or "").strip().upper() == "HOOK")
    accept = sum(1 for c in session.corrections if (c.event_kind or "").lower().find("accept") >= 0)
    reject = sum(1 for c in session.corrections if (c.event_kind or "").lower().find("reject") >= 0)
    sp = timeline.style_profile
    ss = timeline.style_signals
    return EditorialTrainingSummaryViewModel(
        total_scenes=len(timeline.timeline_scenes),
        hooks_detected=hooks,
        pacing_score=float(ss.pacing_score),
        average_pacing=float(sp.average_pacing),
        motion_density=float(sp.motion_density),
        style_visual_dynamism=float(sp.visual_dynamism),
        corrections_applied=len(session.corrections),
        clip_accept_count=accept,
        clip_reject_count=reject,
    )
