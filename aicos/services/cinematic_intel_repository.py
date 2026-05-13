"""Repositorio SQLite para inteligencia cinematográfica (adaptador de infraestructura)."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, TypeVar

from sqlalchemy import delete, select

from aicos.application.cinematic.ports import (
    ClipSemanticMetadataRepositoryPort,
    FeedbackEventRepositoryPort,
    RankingHistoryRepositoryPort,
    SceneAnalysisRepositoryPort,
)
from aicos.database.db import (
    ClipSemanticMetadataRow,
    EmotionAnalysisRow,
    FeedbackEventRow,
    NarrativeAnalysisRow,
    RankingHistoryRow,
    VisualIntentRow,
    session_scope,
)
from aicos.domain.cinematic.entities import (
    ClipSemanticMetadata,
    EmotionAnalysis,
    FeedbackEvent,
    NarrativeClassificationResult,
    VisualIntent,
)
from aicos.domain.cinematic.enums import (
    CameraMovement,
    CameraType,
    CinematicStyle,
    ColorMood,
    EmotionType,
    EnergyLevel,
    EnvironmentType,
    Framing,
    LightingStyle,
    MarketingUsage,
    NarrativeRole,
    Pacing,
    TransitionCompatibility,
    VisualIntentKind,
)

logger = logging.getLogger(__name__)

E = TypeVar("E")


def _enum_or_none(enum_cls: type[E], value: str | None) -> E | None:
    if value is None:
        return None
    try:
        return enum_cls(value)  # type: ignore[return-value]
    except ValueError:
        return None


def _tuple_enums(enum_cls: type, values: list | None) -> tuple:
    if not values:
        return ()
    out: list = []
    for v in values:
        e = _enum_or_none(enum_cls, v) if isinstance(v, str) else v
        if e is not None:
            out.append(e)
    return tuple(out)


def clip_meta_to_payload(meta: ClipSemanticMetadata) -> dict[str, Any]:
    """Serializa metadata completa para columna JSON."""
    return {
        "visual_description": meta.visual_description,
        "primary_emotion": meta.primary_emotion.value if meta.primary_emotion else None,
        "secondary_emotions": [e.value for e in meta.secondary_emotions],
        "energy_level": meta.energy_level.value if meta.energy_level else None,
        "pacing": meta.pacing.value if meta.pacing else None,
        "camera_type": meta.camera_type.value if meta.camera_type else None,
        "camera_movement": meta.camera_movement.value if meta.camera_movement else None,
        "framing": meta.framing.value if meta.framing else None,
        "lighting_style": meta.lighting_style.value if meta.lighting_style else None,
        "color_mood": meta.color_mood.value if meta.color_mood else None,
        "cinematic_style": meta.cinematic_style.value if meta.cinematic_style else None,
        "marketing_usage": meta.marketing_usage.value if meta.marketing_usage else None,
        "narrative_roles": [r.value for r in meta.narrative_roles],
        "visual_intents": list(meta.visual_intents),
        "objects_detected": list(meta.objects_detected),
        "actions_detected": list(meta.actions_detected),
        "people_detected": list(meta.people_detected),
        "environment_type": meta.environment_type.value if meta.environment_type else None,
        "transition_compatibility": meta.transition_compatibility.value
        if meta.transition_compatibility
        else None,
        "hook_strength": meta.hook_strength,
        "cta_strength": meta.cta_strength,
        "emotional_intensity": meta.emotional_intensity,
        "semantic_tags": list(meta.semantic_tags),
        "searchable_keywords": list(meta.searchable_keywords),
        "embedding_vector_id": meta.embedding_vector_id,
        "created_at": meta.created_at.isoformat() if meta.created_at else None,
        "updated_at": meta.updated_at.isoformat() if meta.updated_at else None,
    }


def payload_to_clip_meta(clip_id: str, payload: dict[str, Any]) -> ClipSemanticMetadata:
    def _parse_dt(key: str) -> datetime | None:
        raw = payload.get(key)
        if not raw:
            return None
        if isinstance(raw, datetime):
            return raw
        return datetime.fromisoformat(str(raw).replace("Z", "+00:00"))

    return ClipSemanticMetadata(
        clip_id=clip_id,
        visual_description=str(payload.get("visual_description") or ""),
        primary_emotion=_enum_or_none(EmotionType, payload.get("primary_emotion")),
        secondary_emotions=_tuple_enums(EmotionType, payload.get("secondary_emotions") or []),
        energy_level=_enum_or_none(EnergyLevel, payload.get("energy_level")),
        pacing=_enum_or_none(Pacing, payload.get("pacing")),
        camera_type=_enum_or_none(CameraType, payload.get("camera_type")),
        camera_movement=_enum_or_none(CameraMovement, payload.get("camera_movement")),
        framing=_enum_or_none(Framing, payload.get("framing")),
        lighting_style=_enum_or_none(LightingStyle, payload.get("lighting_style")),
        color_mood=_enum_or_none(ColorMood, payload.get("color_mood")),
        cinematic_style=_enum_or_none(CinematicStyle, payload.get("cinematic_style")),
        marketing_usage=_enum_or_none(MarketingUsage, payload.get("marketing_usage")),
        narrative_roles=_tuple_enums(NarrativeRole, payload.get("narrative_roles") or []),
        visual_intents=tuple(payload.get("visual_intents") or ()),
        objects_detected=tuple(payload.get("objects_detected") or ()),
        actions_detected=tuple(payload.get("actions_detected") or ()),
        people_detected=tuple(payload.get("people_detected") or ()),
        environment_type=_enum_or_none(EnvironmentType, payload.get("environment_type")),
        transition_compatibility=_enum_or_none(
            TransitionCompatibility, payload.get("transition_compatibility")
        ),
        hook_strength=float(payload.get("hook_strength") or 0.0),
        cta_strength=float(payload.get("cta_strength") or 0.0),
        emotional_intensity=float(payload.get("emotional_intensity") or 0.0),
        semantic_tags=tuple(payload.get("semantic_tags") or ()),
        searchable_keywords=tuple(payload.get("searchable_keywords") or ()),
        embedding_vector_id=payload.get("embedding_vector_id"),
        created_at=_parse_dt("created_at"),
        updated_at=_parse_dt("updated_at"),
    )


def visual_intent_to_dict(v: VisualIntent) -> dict[str, Any]:
    return {
        "intent_type": v.intent_type.value,
        "cinematic_priority": v.cinematic_priority,
        "suggested_camera_styles": list(v.suggested_camera_styles),
        "suggested_editing_styles": list(v.suggested_editing_styles),
        "suggested_visual_elements": list(v.suggested_visual_elements),
        "suggested_motion": list(v.suggested_motion),
        "suggested_color_mood": list(v.suggested_color_mood),
        "suggested_transition_style": list(v.suggested_transition_style),
        "suggested_shot_types": list(v.suggested_shot_types),
    }


def visual_intent_from_dict(d: dict[str, Any]) -> VisualIntent:
    return VisualIntent(
        intent_type=VisualIntentKind(d["intent_type"]),
        cinematic_priority=float(d.get("cinematic_priority") or 0.5),
        suggested_camera_styles=tuple(d.get("suggested_camera_styles") or ()),
        suggested_editing_styles=tuple(d.get("suggested_editing_styles") or ()),
        suggested_visual_elements=tuple(d.get("suggested_visual_elements") or ()),
        suggested_motion=tuple(d.get("suggested_motion") or ()),
        suggested_color_mood=tuple(d.get("suggested_color_mood") or ()),
        suggested_transition_style=tuple(d.get("suggested_transition_style") or ()),
        suggested_shot_types=tuple(d.get("suggested_shot_types") or ()),
    )


class SqlCinematicIntelRepository(
    ClipSemanticMetadataRepositoryPort,
    SceneAnalysisRepositoryPort,
    FeedbackEventRepositoryPort,
    RankingHistoryRepositoryPort,
):
    """Persistencia de metadata de clip, análisis de escena, feedback e historial de ranking."""

    def upsert_clip_semantic_metadata(self, meta: ClipSemanticMetadata) -> None:
        payload = clip_meta_to_payload(meta)
        dom_narr = meta.narrative_roles[0].value if meta.narrative_roles else None
        with session_scope() as session:
            row = session.scalars(
                select(ClipSemanticMetadataRow).where(ClipSemanticMetadataRow.clip_id == meta.clip_id)
            ).first()
            if row is None:
                row = ClipSemanticMetadataRow(
                    id=str(uuid.uuid4()),
                    clip_id=meta.clip_id,
                    embedding_vector_id=meta.embedding_vector_id,
                    primary_emotion=meta.primary_emotion.value if meta.primary_emotion else None,
                    energy_level=meta.energy_level.value if meta.energy_level else None,
                    pacing=meta.pacing.value if meta.pacing else None,
                    dominant_narrative_role=dom_narr,
                    payload=payload,
                )
                session.add(row)
            else:
                row.embedding_vector_id = meta.embedding_vector_id
                row.primary_emotion = meta.primary_emotion.value if meta.primary_emotion else None
                row.energy_level = meta.energy_level.value if meta.energy_level else None
                row.pacing = meta.pacing.value if meta.pacing else None
                row.dominant_narrative_role = dom_narr
                row.payload = payload
        logger.debug("cinematic_intel repo=clip_semantic_metadata upsert clip_id=%s", meta.clip_id)

    def get_clip_semantic_metadata(self, clip_id: str) -> ClipSemanticMetadata | None:
        with session_scope() as session:
            row = session.scalars(
                select(ClipSemanticMetadataRow).where(ClipSemanticMetadataRow.clip_id == clip_id)
            ).first()
            if row is None:
                return None
            return payload_to_clip_meta(clip_id, dict(row.payload))

    def save_narrative(
        self, scene_id: str, result: NarrativeClassificationResult, provider: str
    ) -> None:
        with session_scope() as session:
            session.execute(delete(NarrativeAnalysisRow).where(NarrativeAnalysisRow.scene_id == scene_id))
            session.add(
                NarrativeAnalysisRow(
                    id=str(uuid.uuid4()),
                    scene_id=scene_id,
                    narrative_role=result.narrative_role.value,
                    confidence=result.confidence,
                    reasoning=result.reasoning,
                    compatible_visual_styles=list(result.compatible_visual_styles),
                    pacing_recommendation=result.pacing_recommendation,
                    provider=provider,
                )
            )

    def save_emotion(self, scene_id: str, analysis: EmotionAnalysis) -> None:
        with session_scope() as session:
            session.execute(delete(EmotionAnalysisRow).where(EmotionAnalysisRow.scene_id == scene_id))
            payload = {
                "secondary_emotions": [e.value for e in analysis.secondary_emotions],
                "emotional_arc_position": analysis.emotional_arc_position,
                "energy_curve": analysis.energy_curve,
                "emotional_transition": analysis.emotional_transition,
            }
            session.add(
                EmotionAnalysisRow(
                    id=str(uuid.uuid4()),
                    scene_id=scene_id,
                    clip_id=None,
                    primary_emotion=analysis.primary_emotion.value,
                    emotional_intensity=analysis.emotional_intensity,
                    payload=payload,
                )
            )

    def save_visual_intents(self, scene_id: str, intents: tuple[VisualIntent, ...]) -> None:
        data = [visual_intent_to_dict(v) for v in intents]
        with session_scope() as session:
            session.execute(delete(VisualIntentRow).where(VisualIntentRow.scene_id == scene_id))
            session.add(VisualIntentRow(id=str(uuid.uuid4()), scene_id=scene_id, intents_json=data))

    def append_event(self, event: FeedbackEvent) -> None:
        with session_scope() as session:
            session.add(
                FeedbackEventRow(
                    id=event.id,
                    event_type=event.event_type,
                    clip_id=event.clip_id,
                    scene_id=event.scene_id,
                    project_id=event.project_id,
                    rejection_reason=event.rejection_reason,
                    acceptance_score=event.acceptance_score,
                    payload=event.payload,
                )
            )

    def append_ranking(
        self,
        *,
        clip_id: str | None,
        scene_id: str | None,
        final_score: float,
        factors: dict[str, float] | None,
        query_fingerprint: str | None = None,
    ) -> None:
        with session_scope() as session:
            session.add(
                RankingHistoryRow(
                    id=str(uuid.uuid4()),
                    query_fingerprint=query_fingerprint,
                    clip_id=clip_id,
                    scene_id=scene_id,
                    final_score=final_score,
                    factors_json=factors,
                )
            )
