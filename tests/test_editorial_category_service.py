"""Tests del servicio de override de categoría editorial."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from typing import Any

from aicos.application.editorial_category.editorial_category_override_service import (
    EditorialCategoryOverrideService,
)
from aicos.application.editorial_dataset.ports import RawTimelineSceneInput
from aicos.domain.editorial_category.entities import EditorialSceneCategoryOverride


class InMemoryCategoryRepo:
    def __init__(self) -> None:
        self._rows: dict[tuple[str, int], EditorialSceneCategoryOverride] = {}

    def get(self, session: Any, session_id: str, scene_index: int) -> EditorialSceneCategoryOverride | None:
        return self._rows.get((session_id, scene_index))

    def list_by_session(self, session: Any, session_id: str) -> tuple[EditorialSceneCategoryOverride, ...]:
        return tuple(v for (sid, _), v in sorted(self._rows.items()) if sid == session_id)

    def upsert(self, session: Any, override: EditorialSceneCategoryOverride) -> None:
        self._rows[(override.session_id, override.scene_index)] = override


def _raw(idx: int, role: str) -> RawTimelineSceneInput:
    return RawTimelineSceneInput(
        scene_index=idx,
        clip_id=f"c{idx}",
        start_time=0.0,
        end_time=1.0,
        transition_type="cut",
        narrative_role=role,
        motion_intensity=0.5,
        visual_energy=0.5,
        camera_type="",
        semantic_tags=(),
        emotion_tags=(),
    )


def test_human_override_survives_reanalyze():
    repo = InMemoryCategoryRepo()
    svc = EditorialCategoryOverrideService(persistence=repo)
    sid = "sess-1"

    svc.set_human_category(None, sid, 0, "AUTHORITY", auto_fallback="PROBLEM")
    merged = svc.prepare_raw_for_timeline_build(None, sid, (_raw(0, "PROBLEM"),), from_auto_detection=True)
    assert merged[0].narrative_role == "AUTHORITY"


def test_ui_save_persists_override():
    repo = InMemoryCategoryRepo()
    svc = EditorialCategoryOverrideService(persistence=repo)
    sid = "sess-2"

    repo.upsert(
        None,
        EditorialSceneCategoryOverride(
            session_id=sid,
            scene_index=1,
            auto_narrative_role="PROBLEM",
            human_narrative_role=None,
            updated_at=datetime.now(timezone.utc),
        ),
    )
    merged = svc.prepare_raw_for_timeline_build(None, sid, (_raw(1, "AUTHORITY"),), from_auto_detection=False)
    assert merged[0].narrative_role == "AUTHORITY"
    row = repo.get(None, sid, 1)
    assert row is not None
    assert row.human_narrative_role == "AUTHORITY"
    assert row.auto_narrative_role == "PROBLEM"
