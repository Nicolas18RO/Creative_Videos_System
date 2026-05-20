"""Orquestación de intención semántica: taxonomía clip ≠ narrativa audio."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import replace
from datetime import datetime, timezone
from typing import Any

from aicos.application.editorial_dataset.ports import RawTimelineSceneInput
from aicos.application.editorial_semantic_intent.ports import (
    ClipSourceTaxonomyResolverPort,
    EditorialSemanticIntentPersistencePort,
)
from aicos.domain.editorial_dataset.entities import CreativeTimeline, TimelineScene
from aicos.domain.editorial_taxonomy.entities import SceneSemanticIntent
from aicos.domain.editorial_taxonomy.rules import (
    effective_narrative_intent,
    infer_emotional_intent_from_text,
    infer_visual_style_label,
    intent_label_for_role,
    normalize_clip_source_taxonomy,
    normalize_emotional_intent,
    normalize_narrative_intent,
    should_persist_human_override,
    taxonomy_auto_must_not_be_overwritten,
)
from aicos.models.schemas import AnalyzedScene
from aicos.services import library_service

logger = logging.getLogger(__name__)


class EditorialSemanticIntentService:
    def __init__(
        self,
        *,
        persistence: EditorialSemanticIntentPersistencePort,
        clip_taxonomy: ClipSourceTaxonomyResolverPort,
    ) -> None:
        self._persistence = persistence
        self._clip_taxonomy = clip_taxonomy

    def list_by_session(self, session: Any, session_id: str) -> tuple[SceneSemanticIntent, ...]:
        return self._persistence.list_by_session(session, session_id)

    def get_for_scene(self, session: Any, session_id: str, scene_index: int) -> SceneSemanticIntent | None:
        return self._persistence.get(session, session_id, scene_index)

    def seed_from_analysis(
        self,
        session: Any,
        session_id: str,
        analyzed_scenes: Sequence[AnalyzedScene],
    ) -> None:
        """Separa taxonomía del clip (carpeta) de intención narrativa (audio)."""
        for asc in analyzed_scenes:
            sc = asc.scene
            idx = int(sc.scene_index)
            clip_id = asc.recommendations[0].clip_id if asc.recommendations else f"unassigned_{idx}"
            clip_source = self._clip_taxonomy.resolve_clip_source_taxonomy(session, str(clip_id))
            narrative_auto = normalize_narrative_intent(sc.narrative_function)
            emotional_auto = infer_emotional_intent_from_text(sc.text or "", sc.concept or "")
            subcategory = ""
            clip_row = library_service.get_clip_by_id(session, str(clip_id))
            if clip_row is not None:
                subcategory = clip_row.subcategory or ""
            visual = infer_visual_style_label(
                subcategory=subcategory,
                semantic_tags=(sc.concept,) if sc.concept else (),
            )
            existing = self._persistence.get(session, session_id, idx)
            if existing is None:
                row = SceneSemanticIntent(
                    session_id=session_id,
                    scene_index=idx,
                    clip_id=str(clip_id)[:128],
                    auto_clip_source_taxonomy=clip_source,
                    auto_narrative_intent=narrative_auto,
                    auto_emotional_intent=emotional_auto,
                    audio_fragment_text=(sc.text or "").strip()[:4000],
                    visual_style_label=visual,
                    updated_at=datetime.now(timezone.utc),
                    reviewer="system",
                )
            else:
                row = replace(
                    existing,
                    clip_id=str(clip_id)[:128] or existing.clip_id,
                    auto_clip_source_taxonomy=clip_source,
                    auto_narrative_intent=narrative_auto,
                    auto_emotional_intent=emotional_auto,
                    audio_fragment_text=(sc.text or "").strip()[:4000] or existing.audio_fragment_text,
                    visual_style_label=visual or existing.visual_style_label,
                    updated_at=datetime.now(timezone.utc),
                )
            self._persistence.upsert(session, row)
        logger.info("[SemanticIntent] seeded session=%s scenes=%s", session_id, len(analyzed_scenes))

    def set_human_narrative_intent(
        self,
        session: Any,
        session_id: str,
        scene_index: int,
        human_intent: str,
        *,
        reviewer: str = "human",
    ) -> SceneSemanticIntent:
        return self._set_human_axis(
            session,
            session_id,
            scene_index,
            field="narrative",
            human_value=human_intent,
            reviewer=reviewer,
        )

    def set_human_clip_source_taxonomy(
        self,
        session: Any,
        session_id: str,
        scene_index: int,
        human_taxonomy: str,
        *,
        reviewer: str = "human",
    ) -> SceneSemanticIntent:
        return self._set_human_axis(
            session,
            session_id,
            scene_index,
            field="clip_source",
            human_value=human_taxonomy,
            reviewer=reviewer,
        )

    def set_human_emotional_intent(
        self,
        session: Any,
        session_id: str,
        scene_index: int,
        human_emotional: str,
        *,
        reviewer: str = "human",
    ) -> SceneSemanticIntent:
        return self._set_human_axis(
            session,
            session_id,
            scene_index,
            field="emotional",
            human_value=human_emotional,
            reviewer=reviewer,
        )

    def _set_human_axis(
        self,
        session: Any,
        session_id: str,
        scene_index: int,
        *,
        field: str,
        human_value: str,
        reviewer: str,
    ) -> SceneSemanticIntent:
        existing = self._persistence.get(session, session_id, scene_index)
        if existing is None:
            existing = SceneSemanticIntent(
                session_id=session_id,
                scene_index=int(scene_index),
                updated_at=datetime.now(timezone.utc),
            )
        if field == "narrative":
            auto = existing.auto_narrative_intent
            human = normalize_narrative_intent(human_value)
            stored = (
                human
                if should_persist_human_override(auto, human, normalizer=normalize_narrative_intent)
                else None
            )
            row = replace(
                existing,
                human_narrative_intent=stored,
                updated_at=datetime.now(timezone.utc),
                reviewer=reviewer,
            )
        elif field == "clip_source":
            auto = existing.auto_clip_source_taxonomy
            human = normalize_clip_source_taxonomy(human_value)
            stored = (
                human
                if should_persist_human_override(auto, human, normalizer=normalize_clip_source_taxonomy)
                else None
            )
            row = replace(
                existing,
                human_clip_source_taxonomy=stored,
                updated_at=datetime.now(timezone.utc),
                reviewer=reviewer,
            )
        else:
            auto = existing.auto_emotional_intent
            human = normalize_emotional_intent(human_value)
            stored = (
                human
                if should_persist_human_override(auto, human, normalizer=normalize_emotional_intent)
                else None
            )
            row = replace(
                existing,
                human_emotional_intent=stored,
                updated_at=datetime.now(timezone.utc),
                reviewer=reviewer,
            )
        self._persistence.upsert(session, row)
        return row

    def prepare_raw_for_timeline_build(
        self,
        session: Any,
        session_id: str,
        raw_scenes: tuple[RawTimelineSceneInput, ...],
        *,
        from_auto_detection: bool = False,
    ) -> tuple[RawTimelineSceneInput, ...]:
        """Timeline usa intención narrativa efectiva; nunca mezcla con taxonomía del clip."""
        by_idx = {o.scene_index: o for o in self._persistence.list_by_session(session, session_id)}
        out: list[RawTimelineSceneInput] = []
        for r in raw_scenes:
            detected_narrative = normalize_narrative_intent(r.narrative_role)
            clip_source = self._clip_taxonomy.resolve_clip_source_taxonomy(session, r.clip_id)
            existing = by_idx.get(r.scene_index)
            if existing is None:
                narrative_auto = detected_narrative
                human_narrative: str | None = None
                if not from_auto_detection and should_persist_human_override(
                    narrative_auto, detected_narrative, normalizer=normalize_narrative_intent
                ):
                    human_narrative = detected_narrative
                self._persistence.upsert(
                    session,
                    SceneSemanticIntent(
                        session_id=session_id,
                        scene_index=r.scene_index,
                        clip_id=r.clip_id,
                        auto_clip_source_taxonomy=clip_source,
                        human_clip_source_taxonomy=None,
                        auto_narrative_intent=narrative_auto,
                        human_narrative_intent=human_narrative,
                        auto_emotional_intent=infer_emotional_intent_from_text(""),
                        updated_at=datetime.now(timezone.utc),
                        reviewer="human" if human_narrative else "system",
                    ),
                )
                role = effective_narrative_intent(narrative_auto, human_narrative)
            else:
                clip_auto = (
                    clip_source
                    if from_auto_detection
                    else taxonomy_auto_must_not_be_overwritten(
                        existing.auto_clip_source_taxonomy,
                        clip_source,
                        normalizer=normalize_clip_source_taxonomy,
                    )
                )
                narrative_auto = taxonomy_auto_must_not_be_overwritten(
                    existing.auto_narrative_intent,
                    detected_narrative if from_auto_detection else existing.auto_narrative_intent,
                    normalizer=normalize_narrative_intent,
                )
                human_narrative = existing.human_narrative_intent
                if (
                    not from_auto_detection
                    and human_narrative is None
                    and should_persist_human_override(
                        narrative_auto, detected_narrative, normalizer=normalize_narrative_intent
                    )
                ):
                    human_narrative = detected_narrative
                self._persistence.upsert(
                    session,
                    replace(
                        existing,
                        clip_id=r.clip_id or existing.clip_id,
                        auto_clip_source_taxonomy=clip_auto,
                        auto_narrative_intent=narrative_auto,
                        human_narrative_intent=human_narrative,
                        updated_at=datetime.now(timezone.utc),
                    ),
                )
                role = effective_narrative_intent(narrative_auto, human_narrative)
            if role != r.narrative_role:
                out.append(replace(r, narrative_role=role))
            else:
                out.append(r)
        return tuple(out)

    def apply_to_timeline(self, session: Any, session_id: str, timeline: CreativeTimeline) -> CreativeTimeline:
        by_idx = {o.scene_index: o for o in self._persistence.list_by_session(session, session_id)}
        scenes: list[TimelineScene] = []
        for sc in timeline.timeline_scenes:
            intent = by_idx.get(sc.scene_index)
            if intent is None:
                clip_source = self._clip_taxonomy.resolve_clip_source_taxonomy(session, sc.clip_id)
                intent = SceneSemanticIntent(
                    session_id=session_id,
                    scene_index=sc.scene_index,
                    clip_id=sc.clip_id,
                    auto_clip_source_taxonomy=clip_source,
                    auto_narrative_intent=normalize_narrative_intent(sc.narrative_role),
                    updated_at=datetime.now(timezone.utc),
                )
                self._persistence.upsert(session, intent)
            role = intent.effective_narrative_intent
            if role != sc.narrative_role:
                scenes.append(replace(sc, narrative_role=role))
            else:
                scenes.append(sc)
        return replace(timeline, timeline_scenes=tuple(scenes))

    def merge_semantic_intents_after_scene_merge(
        self,
        session: Any,
        session_id: str,
        *,
        source_scene_index_a: int,
        source_scene_index_b: int,
        merged_scene: TimelineScene,
        old_to_new_index: dict[int, int],
    ) -> None:
        """Consolida anotaciones semánticas y reindexa tras fusión de escenas."""
        by_idx = {o.scene_index: o for o in self._persistence.list_by_session(session, session_id)}
        left = by_idx.get(source_scene_index_a)
        right = by_idx.get(source_scene_index_b)
        audio_parts = [
            (left.audio_fragment_text if left else "").strip(),
            (right.audio_fragment_text if right else "").strip(),
        ]
        combined_audio = " · ".join(p for p in audio_parts if p)[:4000]
        auto_clip = (left.auto_clip_source_taxonomy if left else "") or (right.auto_clip_source_taxonomy if right else "")
        auto_narrative = normalize_narrative_intent(merged_scene.narrative_role)
        human_narrative = (left.human_narrative_intent if left else None) or (
            right.human_narrative_intent if right else None
        )
        emotional = infer_emotional_intent_from_text(combined_audio)
        visual = (left.visual_style_label if left else "") or (right.visual_style_label if right else "")

        for old_idx, intent in list(by_idx.items()):
            if old_idx in (source_scene_index_a, source_scene_index_b):
                continue
            new_i = old_to_new_index.get(old_idx)
            if new_i is None:
                continue
            self._persistence.upsert(session, replace(intent, scene_index=new_i, session_id=session_id))

        merged_i = old_to_new_index.get(source_scene_index_a)
        if merged_i is None:
            merged_i = old_to_new_index.get(source_scene_index_b, 0)
        self._persistence.upsert(
            session,
            SceneSemanticIntent(
                session_id=session_id,
                scene_index=int(merged_i),
                clip_id=merged_scene.clip_id,
                auto_clip_source_taxonomy=normalize_clip_source_taxonomy(auto_clip or auto_narrative),
                human_clip_source_taxonomy=left.human_clip_source_taxonomy if left else None,
                auto_narrative_intent=auto_narrative,
                human_narrative_intent=human_narrative,
                auto_emotional_intent=emotional,
                human_emotional_intent=(
                    left.human_emotional_intent if left and left.human_emotional_intent else None
                )
                or (right.human_emotional_intent if right else None),
                audio_fragment_text=combined_audio,
                visual_style_label=visual,
                updated_at=datetime.now(timezone.utc),
                reviewer="system",
            ),
        )
