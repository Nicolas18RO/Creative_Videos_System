"""Persistencia SQLite de intención semántica por escena."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from aicos.application.editorial_semantic_intent.ports import EditorialSemanticIntentPersistencePort
from aicos.database.db import EditorialSceneSemanticIntentRow
from aicos.domain.editorial_taxonomy.entities import SceneSemanticIntent


def _aware(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _to_entity(row: EditorialSceneSemanticIntentRow) -> SceneSemanticIntent:
    return SceneSemanticIntent(
        session_id=row.session_id,
        scene_index=int(row.scene_index),
        clip_id=row.clip_id or "",
        auto_clip_source_taxonomy=row.auto_clip_source_taxonomy or "NATURAL",
        human_clip_source_taxonomy=row.human_clip_source_taxonomy,
        auto_narrative_intent=row.auto_narrative_intent or "NATURAL",
        human_narrative_intent=row.human_narrative_intent,
        auto_emotional_intent=row.auto_emotional_intent or "NEUTRAL",
        human_emotional_intent=row.human_emotional_intent,
        audio_fragment_text=row.audio_fragment_text or "",
        visual_style_label=row.visual_style_label or "",
        updated_at=_aware(row.updated_at),
        reviewer=row.reviewer or "system",
    )


class SqlEditorialSemanticIntentRepository(EditorialSemanticIntentPersistencePort):
    def get(self, session: Session, session_id: str, scene_index: int) -> SceneSemanticIntent | None:
        row = session.scalar(
            select(EditorialSceneSemanticIntentRow).where(
                EditorialSceneSemanticIntentRow.session_id == session_id,
                EditorialSceneSemanticIntentRow.scene_index == scene_index,
            )
        )
        return _to_entity(row) if row else None

    def list_by_session(self, session: Session, session_id: str) -> tuple[SceneSemanticIntent, ...]:
        rows = session.scalars(
            select(EditorialSceneSemanticIntentRow)
            .where(EditorialSceneSemanticIntentRow.session_id == session_id)
            .order_by(EditorialSceneSemanticIntentRow.scene_index)
        ).all()
        return tuple(_to_entity(r) for r in rows)

    def upsert(self, session: Session, intent: SceneSemanticIntent) -> None:
        row = session.scalar(
            select(EditorialSceneSemanticIntentRow).where(
                EditorialSceneSemanticIntentRow.session_id == intent.session_id,
                EditorialSceneSemanticIntentRow.scene_index == intent.scene_index,
            )
        )
        if row is None:
            row = EditorialSceneSemanticIntentRow(
                id=str(uuid.uuid4()),
                session_id=intent.session_id,
                scene_index=intent.scene_index,
                clip_id=intent.clip_id,
                auto_clip_source_taxonomy=intent.auto_clip_source_taxonomy,
                human_clip_source_taxonomy=intent.human_clip_source_taxonomy,
                auto_narrative_intent=intent.auto_narrative_intent,
                human_narrative_intent=intent.human_narrative_intent,
                auto_emotional_intent=intent.auto_emotional_intent,
                human_emotional_intent=intent.human_emotional_intent,
                audio_fragment_text=intent.audio_fragment_text,
                visual_style_label=intent.visual_style_label,
                reviewer=intent.reviewer,
            )
            session.add(row)
        else:
            row.clip_id = intent.clip_id
            row.auto_clip_source_taxonomy = intent.auto_clip_source_taxonomy
            row.human_clip_source_taxonomy = intent.human_clip_source_taxonomy
            row.auto_narrative_intent = intent.auto_narrative_intent
            row.human_narrative_intent = intent.human_narrative_intent
            row.auto_emotional_intent = intent.auto_emotional_intent
            row.human_emotional_intent = intent.human_emotional_intent
            row.audio_fragment_text = intent.audio_fragment_text
            row.visual_style_label = intent.visual_style_label
            row.reviewer = intent.reviewer
        session.flush()
