"""Tests servicio de intención semántica."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from aicos.application.editorial_dataset.ports import RawTimelineSceneInput
from aicos.application.editorial_semantic_intent.editorial_semantic_intent_service import EditorialSemanticIntentService
from aicos.domain.editorial_taxonomy.entities import SceneSemanticIntent


class InMemorySemanticRepo:
    def __init__(self) -> None:
        self._rows: dict[tuple[str, int], SceneSemanticIntent] = {}

    def get(self, session: Any, session_id: str, scene_index: int) -> SceneSemanticIntent | None:
        return self._rows.get((session_id, scene_index))

    def list_by_session(self, session: Any, session_id: str) -> tuple[SceneSemanticIntent, ...]:
        return tuple(v for (sid, _), v in sorted(self._rows.items()) if sid == session_id)

    def upsert(self, session: Any, intent: SceneSemanticIntent) -> None:
        self._rows[(intent.session_id, intent.scene_index)] = intent


class StubClipResolver:
    def resolve_clip_source_taxonomy(self, session: Any, clip_id: str) -> str:
        if clip_id == "auth_clip":
            return "AUTHORITY"
        return "NATURAL"


def _raw(role: str, clip_id: str = "auth_clip") -> RawTimelineSceneInput:
    return RawTimelineSceneInput(
        scene_index=0,
        clip_id=clip_id,
        start_time=0.0,
        end_time=2.0,
        transition_type="cut",
        narrative_role=role,
        motion_intensity=0.5,
        visual_energy=0.5,
        camera_type="",
        semantic_tags=(),
        emotion_tags=(),
    )


def test_timeline_uses_narrative_intent_not_clip_folder():
    repo = InMemorySemanticRepo()
    svc = EditorialSemanticIntentService(persistence=repo, clip_taxonomy=StubClipResolver())
    sid = "s1"
    repo.upsert(
        None,
        SceneSemanticIntent(
            session_id=sid,
            scene_index=0,
            clip_id="auth_clip",
            auto_clip_source_taxonomy="AUTHORITY",
            auto_narrative_intent="PROBLEM",
            human_narrative_intent="PROBLEM",
            updated_at=datetime.now(timezone.utc),
        ),
    )
    merged = svc.prepare_raw_for_timeline_build(None, sid, (_raw("AUTHORITY"),), from_auto_detection=False)
    assert merged[0].narrative_role == "PROBLEM"
