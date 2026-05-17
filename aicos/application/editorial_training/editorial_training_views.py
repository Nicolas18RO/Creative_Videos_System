"""Construcción de DTOs de presentación para el workspace de entrenamiento editorial."""

from __future__ import annotations

from aicos.application.editorial_review.presentation import apply_review_to_scene_card, build_review_lookup
from aicos.application.timeline_visualization.presentation import media_url
from aicos.domain.editorial_dataset.entities import CreativeTimeline, TimelineScene
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


def _scene_type_label(narrative_role: str) -> str:
    nr = (narrative_role or "").strip().upper()
    if nr == "HOOK":
        return "Hook Scene"
    if nr == "CTA":
        return "Call To Action"
    if nr:
        return nr.replace("_", " ").title()
    return "Scene"


def build_timeline_scene_cards(
    timeline: CreativeTimeline,
    *,
    visual_previews: tuple[TimelineClipPreview, ...] | None = None,
    creative_id: str | None = None,
    review_states: tuple[EditorialSceneReviewState, ...] | None = None,
) -> list[TimelineSceneViewModel]:
    cid = creative_id or timeline.creative_id
    by_idx = {p.scene_index: p for p in visual_previews} if visual_previews else {}
    reviews = build_review_lookup(review_states) if review_states else {}
    out: list[TimelineSceneViewModel] = []
    for s in timeline.timeline_scenes:
        card = _scene_to_card(s, cid, by_idx.get(s.scene_index))
        rev = reviews.get(scene_id_from_index(s.scene_index))
        out.append(apply_review_to_scene_card(card, s, rev))
    return out


def _scene_to_card(
    s: TimelineScene,
    creative_id: str,
    preview: TimelineClipPreview | None,
) -> TimelineSceneViewModel:
    thumb = ""
    prev = ""
    if preview is not None:
        if preview.thumbnail_path:
            thumb = media_url(creative_id, s.scene_index, "thumbnail")
        if preview.preview_video_path:
            prev = media_url(creative_id, s.scene_index, "preview")
    return TimelineSceneViewModel(
        scene_index=s.scene_index,
        thumbnail_url=thumb,
        preview_video_url=prev,
        hook_score=hook_probability_for_scene(s),
        review_status="pending",
        confidence_score=hook_probability_for_scene(s),
        scene_type_label=_scene_type_label(s.narrative_role),
        narrative_role=s.narrative_role,
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
