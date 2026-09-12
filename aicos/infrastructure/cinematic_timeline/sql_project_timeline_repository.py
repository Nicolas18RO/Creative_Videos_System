"""Persistencia SQLite de timeline de proyecto (escenas M1)."""

from __future__ import annotations

from sqlalchemy import delete, select

from aicos.database.db import GapRow, RecommendationRow, SceneRow
from aicos.domain.cinematic_timeline.entities import ProjectTimelineScene


class SqlProjectTimelineRepository:
    def load_timeline(self, session, project_id: str) -> tuple[ProjectTimelineScene, ...]:
        rows = session.scalars(
            select(SceneRow).where(SceneRow.project_id == project_id).order_by(SceneRow.scene_index)
        ).all()
        return tuple(self._row_to_entity(r) for r in rows)

    def project_duration_ms(self, session, project_id: str) -> int:
        scenes = self.load_timeline(session, project_id)
        if not scenes:
            return 0
        return max(s.end_ms for s in scenes)

    def replace_timeline(
        self,
        session,
        project_id: str,
        scenes: tuple[ProjectTimelineScene, ...],
        *,
        deleted_scene_ids: tuple[str, ...] = (),
    ) -> None:
        for sid in deleted_scene_ids:
            session.execute(delete(RecommendationRow).where(RecommendationRow.scene_id == sid))
            session.execute(delete(GapRow).where(GapRow.scene_id == sid))
            session.execute(delete(SceneRow).where(SceneRow.id == sid, SceneRow.project_id == project_id))

        for s in scenes:
            row = session.get(SceneRow, s.scene_id)
            if row is None:
                row = SceneRow(
                    id=s.scene_id,
                    project_id=project_id,
                    scene_index=s.scene_index,
                    start_ms=s.start_ms,
                    end_ms=s.end_ms,
                    duration_ms=s.duration_ms,
                    text=s.text,
                    concept=s.concept,
                    narrative_function=s.narrative_function,
                    is_hook=s.is_hook,
                    gender_hint=s.gender_hint,
                    selected_clip_id=s.selected_clip_id,
                    gap_detected=False,
                )
                session.add(row)
            else:
                row.scene_index = s.scene_index
                row.start_ms = s.start_ms
                row.end_ms = s.end_ms
                row.duration_ms = s.duration_ms
                row.text = s.text
                row.concept = s.concept
                row.narrative_function = s.narrative_function
                row.is_hook = s.is_hook
                row.gender_hint = s.gender_hint
                row.selected_clip_id = s.selected_clip_id
        session.flush()

    @staticmethod
    def _row_to_entity(r: SceneRow) -> ProjectTimelineScene:
        return ProjectTimelineScene(
            scene_id=r.id,
            scene_index=r.scene_index,
            start_ms=r.start_ms,
            end_ms=r.end_ms,
            duration_ms=r.duration_ms,
            text=r.text or "",
            concept=r.concept or "",
            narrative_function=r.narrative_function or "NATURAL",
            is_hook=bool(r.is_hook),
            gender_hint=r.gender_hint,
            selected_clip_id=r.selected_clip_id,
        )
