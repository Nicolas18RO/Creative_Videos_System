"""Persistencia SQLite de sesiones de entrenamiento editorial (Fase 6.7)."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from aicos.application.editorial_training.ports import EditorialTrainingSessionPersistencePort
from aicos.database.db import EditorialTrainingSessionRow
from aicos.domain.editorial_training.entities import EditorialTrainingCorrectionItem, EditorialTrainingSession

logger = logging.getLogger(__name__)


def _corrections_to_json(items: tuple[EditorialTrainingCorrectionItem, ...]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for it in items:
        out.append(
            {
                "event_kind": it.event_kind,
                "reward": float(it.reward),
                "clip_id": it.clip_id,
                "replaced_clip_id": it.replaced_clip_id,
                "scene_index": it.scene_index,
                "narrative_function": it.narrative_function,
                "transition_type": it.transition_type,
            }
        )
    return out


def _corrections_from_json(raw: list | None) -> tuple[EditorialTrainingCorrectionItem, ...]:
    if not raw:
        return ()
    items: list[EditorialTrainingCorrectionItem] = []
    for d in raw:
        if not isinstance(d, dict):
            continue
        items.append(
            EditorialTrainingCorrectionItem(
                event_kind=str(d.get("event_kind") or "generic")[:48],
                reward=float(d.get("reward") or 0.0),
                clip_id=(str(d["clip_id"]).strip() or None) if d.get("clip_id") else None,
                replaced_clip_id=(str(d["replaced_clip_id"]).strip() or None) if d.get("replaced_clip_id") else None,
                scene_index=int(d["scene_index"]) if d.get("scene_index") is not None else None,
                narrative_function=(str(d["narrative_function"]).strip() or None)
                if d.get("narrative_function")
                else None,
                transition_type=(str(d["transition_type"]).strip() or None) if d.get("transition_type") else None,
            )
        )
    return tuple(items)


def _aware_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _utc_naive(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


def _meta_labels(meta: dict | None) -> tuple[str, str, str, str]:
    if not isinstance(meta, dict):
        return ("", "", "", "")
    return (
        str(meta.get("project_label") or "")[:512],
        str(meta.get("creative_label") or "")[:512],
        str(meta.get("product_category") or "")[:256],
        str(meta.get("notes") or "")[:4000],
    )


def _meta_from_training(training: EditorialTrainingSession) -> dict[str, Any]:
    return {
        "project_label": training.project_label,
        "creative_label": training.creative_label,
        "product_category": training.product_category,
        "notes": training.notes,
    }


def _row_to_domain(row: EditorialTrainingSessionRow) -> EditorialTrainingSession:
    created = row.created_at or datetime.now(timezone.utc)
    updated = row.updated_at or created
    pl, cl, pc, nt = _meta_labels(row.meta_json if isinstance(row.meta_json, dict) else None)
    return EditorialTrainingSession(
        session_id=row.id,
        creative_id=row.creative_id,
        project_id=row.project_id,
        status=row.status or "draft",
        final_video_path=row.final_video_path or "",
        audio_path=row.audio_path or "",
        corrections=_corrections_from_json(row.corrections_json if isinstance(row.corrections_json, list) else None),
        created_at=_aware_utc(created),
        updated_at=_aware_utc(updated),
        project_label=pl,
        creative_label=cl,
        product_category=pc,
        notes=nt,
    )


class SqlEditorialTrainingSessionRepository(EditorialTrainingSessionPersistencePort):
    def get_by_id(self, session: Session, session_id: str) -> EditorialTrainingSession | None:
        row = session.get(EditorialTrainingSessionRow, session_id)
        if row is None:
            return None
        return _row_to_domain(row)

    def save(self, session: Session, training: EditorialTrainingSession) -> None:
        row = session.get(EditorialTrainingSessionRow, training.session_id)
        cj = _corrections_to_json(training.corrections)
        mj = _meta_from_training(training)
        if row is None:
            row = EditorialTrainingSessionRow(
                id=training.session_id,
                creative_id=training.creative_id,
                project_id=training.project_id,
                status=training.status,
                final_video_path=training.final_video_path,
                audio_path=training.audio_path,
                corrections_json=cj,
                meta_json=mj,
                created_at=_utc_naive(training.created_at),
                updated_at=_utc_naive(training.updated_at),
            )
            session.add(row)
        else:
            row.creative_id = training.creative_id
            row.project_id = training.project_id
            row.status = training.status
            row.final_video_path = training.final_video_path
            row.audio_path = training.audio_path
            row.corrections_json = cj
            row.meta_json = mj
            row.updated_at = _utc_naive(training.updated_at)
        session.flush()
        logger.debug("[EditorialTraining] saved session=%s status=%s", training.session_id, training.status)
