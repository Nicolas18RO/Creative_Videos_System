"""Servicio de overrides de categoría editorial (Fase 6.7.X)."""

from __future__ import annotations

import logging
from dataclasses import replace
from datetime import datetime, timezone
from typing import Any

from aicos.application.editorial_category.ports import EditorialCategoryOverridePersistencePort
from aicos.application.editorial_dataset.ports import RawTimelineSceneInput
from aicos.domain.editorial_category.entities import EditorialSceneCategoryOverride
from aicos.domain.editorial_category.rules import (
    auto_role_must_not_be_overwritten,
    effective_narrative_role,
    normalize_narrative_role,
    should_persist_human_override,
)
from aicos.domain.editorial_dataset.entities import CreativeTimeline, TimelineScene

logger = logging.getLogger(__name__)


class EditorialCategoryOverrideService:
    def __init__(self, *, persistence: EditorialCategoryOverridePersistencePort) -> None:
        self._persistence = persistence

    def list_by_session(self, session: Any, session_id: str) -> tuple[EditorialSceneCategoryOverride, ...]:
        return self._persistence.list_by_session(session, session_id)

    def set_human_category(
        self,
        session: Any,
        session_id: str,
        scene_index: int,
        human_role: str,
        *,
        reviewer: str = "human",
        auto_fallback: str | None = None,
    ) -> EditorialSceneCategoryOverride:
        existing = self._persistence.get(session, session_id, scene_index)
        auto = auto_role_must_not_be_overwritten(
            existing.auto_narrative_role if existing else "",
            auto_fallback or human_role,
        )
        human = normalize_narrative_role(human_role)
        human_stored: str | None = human if should_persist_human_override(auto, human) else None
        row = EditorialSceneCategoryOverride(
            session_id=session_id,
            scene_index=int(scene_index),
            auto_narrative_role=auto,
            human_narrative_role=human_stored,
            updated_at=datetime.now(timezone.utc),
            reviewer=reviewer,
        )
        self._persistence.upsert(session, row)
        logger.info(
            "[EditorialCategory] human_override session=%s scene=%s auto=%s human=%s effective=%s",
            session_id,
            scene_index,
            auto,
            human_stored,
            row.effective_role,
        )
        return row

    def seed_auto_from_timeline(self, session: Any, session_id: str, timeline: CreativeTimeline) -> None:
        """Registra roles auto detectados sin borrar overrides humanos existentes."""
        for sc in timeline.timeline_scenes:
            existing = self._persistence.get(session, session_id, sc.scene_index)
            auto = normalize_narrative_role(sc.narrative_role)
            if existing is None:
                self._persistence.upsert(
                    session,
                    EditorialSceneCategoryOverride(
                        session_id=session_id,
                        scene_index=sc.scene_index,
                        auto_narrative_role=auto,
                        human_narrative_role=None,
                        updated_at=datetime.now(timezone.utc),
                        reviewer="system",
                    ),
                )
            else:
                preserved_auto = auto_role_must_not_be_overwritten(existing.auto_narrative_role, auto)
                if preserved_auto != existing.auto_narrative_role:
                    self._persistence.upsert(
                        session,
                        replace(existing, auto_narrative_role=preserved_auto, updated_at=datetime.now(timezone.utc)),
                    )

    def apply_overrides_to_timeline(
        self,
        session: Any,
        session_id: str,
        timeline: CreativeTimeline,
    ) -> CreativeTimeline:
        """Aplica effective_role a cada escena del timeline antes de persistir o presentar."""
        by_idx = {o.scene_index: o for o in self._persistence.list_by_session(session, session_id)}
        scenes: list[TimelineScene] = []
        for sc in timeline.timeline_scenes:
            ov = by_idx.get(sc.scene_index)
            if ov is None:
                auto = normalize_narrative_role(sc.narrative_role)
                self._persistence.upsert(
                    session,
                    EditorialSceneCategoryOverride(
                        session_id=session_id,
                        scene_index=sc.scene_index,
                        auto_narrative_role=auto,
                        human_narrative_role=None,
                        updated_at=datetime.now(timezone.utc),
                        reviewer="system",
                    ),
                )
                role = auto
            else:
                role = effective_narrative_role(ov.auto_narrative_role, ov.human_narrative_role)
            if role != sc.narrative_role:
                scenes.append(replace(sc, narrative_role=role))
            else:
                scenes.append(sc)
        return replace(timeline, timeline_scenes=tuple(scenes))

    def prepare_raw_for_timeline_build(
        self,
        session: Any,
        session_id: str,
        raw_scenes: tuple[RawTimelineSceneInput, ...],
        *,
        from_auto_detection: bool = False,
    ) -> tuple[RawTimelineSceneInput, ...]:
        """Fusiona detección automática con overrides humanos; nunca pierde la decisión humana."""
        by_idx = {o.scene_index: o for o in self._persistence.list_by_session(session, session_id)}
        out: list[RawTimelineSceneInput] = []
        for r in raw_scenes:
            detected = normalize_narrative_role(r.narrative_role)
            existing = by_idx.get(r.scene_index)
            if existing is None:
                auto = detected
                human: str | None = None
                if not from_auto_detection and should_persist_human_override(auto, detected):
                    human = detected
                self._persistence.upsert(
                    session,
                    EditorialSceneCategoryOverride(
                        session_id=session_id,
                        scene_index=r.scene_index,
                        auto_narrative_role=auto,
                        human_narrative_role=human,
                        updated_at=datetime.now(timezone.utc),
                        reviewer="human" if human else "system",
                    ),
                )
            else:
                auto = auto_role_must_not_be_overwritten(
                    existing.auto_narrative_role,
                    detected if from_auto_detection else existing.auto_narrative_role,
                )
                human = existing.human_narrative_role
                if not from_auto_detection and should_persist_human_override(auto, detected):
                    human = detected
                    self._persistence.upsert(
                        session,
                        replace(
                            existing,
                            auto_narrative_role=auto,
                            human_narrative_role=human,
                            updated_at=datetime.now(timezone.utc),
                            reviewer="human",
                        ),
                    )
                elif auto != existing.auto_narrative_role:
                    self._persistence.upsert(
                        session,
                        replace(existing, auto_narrative_role=auto, updated_at=datetime.now(timezone.utc)),
                    )
            role = effective_narrative_role(auto, human)
            if role != r.narrative_role:
                out.append(replace(r, narrative_role=role))
            else:
                out.append(r)
        return tuple(out)

    def effective_role_for_scene(
        self,
        session: Any,
        session_id: str,
        scene_index: int,
        *,
        timeline_fallback: str = "NATURAL",
    ) -> str:
        ov = self._persistence.get(session, session_id, scene_index)
        if ov is None:
            return normalize_narrative_role(timeline_fallback)
        return effective_narrative_role(ov.auto_narrative_role, ov.human_narrative_role)
