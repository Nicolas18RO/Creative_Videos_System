"""Repositorio SQLite: timelines creativos (solo mapeo ORM ↔ dominio)."""

from __future__ import annotations

import logging
import uuid
from dataclasses import replace
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from aicos.application.editorial_dataset.ports import (
    CreativeTimelinePersistenceReadPort,
    CreativeTimelinePersistenceWritePort,
)
from aicos.database.db import (
    CreativeStyleProfileRow,
    CreativeTimelineRow,
    EditorialPatternRow,
    TimelineSceneRow,
)
from aicos.domain.editorial_dataset.entities import (
    CreativeStyleProfile,
    CreativeTimeline,
    EditorialPattern,
    EditorialStyleSignals,
    TimelineScene,
)

logger = logging.getLogger(__name__)


def _to_scene(row: TimelineSceneRow) -> TimelineScene:
    sem = tuple(row.semantic_tags_json or [])
    emo = tuple(row.emotion_tags_json or [])
    return TimelineScene(
        scene_index=row.scene_index,
        clip_id=row.clip_id,
        start_time=row.start_time_sec,
        end_time=row.end_time_sec,
        duration=row.duration_sec,
        transition_type=row.transition_type or "",
        narrative_role=row.narrative_role or "",
        motion_intensity=float(row.motion_intensity),
        visual_energy=float(row.visual_energy),
        camera_type=row.camera_type or "",
        semantic_tags=tuple(str(x) for x in sem),
        emotion_tags=tuple(str(x) for x in emo),
    )


def _to_domain(
    trow: CreativeTimelineRow,
    scenes: list[TimelineSceneRow],
    prow: CreativeStyleProfileRow | None,
    patterns: list[EditorialPatternRow],
) -> CreativeTimeline:
    from aicos.application.editorial_pattern_engine.serialization import report_from_jsonable

    scene_dom = tuple(_to_scene(s) for s in sorted(scenes, key=lambda x: x.scene_index))
    if prow is None:
        profile = CreativeStyleProfile(
            hook_intensity=0.0,
            average_pacing=0.0,
            motion_density=0.0,
            transition_density=0.0,
            narrative_aggressiveness=0.0,
            visual_dynamism=0.0,
            cinematic_style_tags=(),
        )
        signals = EditorialStyleSignals(
            pacing_score=0.0,
            hook_strength=0.0,
            emotional_curve=(),
            visual_dynamism=0.0,
        )
    else:
        tags = tuple(str(x) for x in (prow.cinematic_style_tags_json or []))
        curve = tuple(float(x) for x in (prow.emotional_curve_json or []))
        profile = CreativeStyleProfile(
            hook_intensity=float(prow.hook_intensity),
            average_pacing=float(prow.average_pacing),
            motion_density=float(prow.motion_density),
            transition_density=float(prow.transition_density),
            narrative_aggressiveness=float(prow.narrative_aggressiveness),
            visual_dynamism=float(prow.visual_dynamism),
            cinematic_style_tags=tags,
        )
        signals = EditorialStyleSignals(
            pacing_score=float(prow.pacing_score),
            hook_strength=float(prow.hook_strength),
            emotional_curve=curve,
            visual_dynamism=float(prow.visual_dynamism),
        )
    pat_dom = tuple(
        EditorialPattern(
            pattern_id=p.pattern_id,
            pattern_type=p.pattern_type,
            pattern_sequence=tuple(str(x) for x in (p.pattern_sequence_json or [])),
            frequency=float(p.frequency),
            confidence_score=float(p.confidence_score),
        )
        for p in patterns
    )
    created = trow.created_at
    if created is not None and created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    report = report_from_jsonable(
        trow.pattern_engine_report_json
        if isinstance(trow.pattern_engine_report_json, dict)
        else None
    )
    return CreativeTimeline(
        creative_id=trow.creative_id,
        audio_path=trow.audio_path or "",
        final_video_path=trow.final_video_path or "",
        timeline_scenes=scene_dom,
        style_profile=profile,
        style_signals=signals,
        editorial_patterns=pat_dom,
        hook_detection=report.hooks if report else (),
        created_at=created,
        dataset_version=int(trow.dataset_version or 1),
        pattern_engine_report=report,
    )


class SqlCreativeTimelineRepository(CreativeTimelinePersistenceReadPort, CreativeTimelinePersistenceWritePort):
    def get_by_creative_id(self, session: Session, creative_id: str) -> CreativeTimeline | None:
        trow = session.scalars(
            select(CreativeTimelineRow).where(CreativeTimelineRow.creative_id == creative_id)
        ).first()
        if trow is None:
            return None
        scenes = list(
            session.scalars(
                select(TimelineSceneRow)
                .where(TimelineSceneRow.creative_timeline_id == trow.id)
                .order_by(TimelineSceneRow.scene_index)
            ).all()
        )
        prow = session.scalars(
            select(CreativeStyleProfileRow).where(
                CreativeStyleProfileRow.creative_timeline_id == trow.id
            )
        ).first()
        patterns = list(
            session.scalars(
                select(EditorialPatternRow).where(EditorialPatternRow.creative_timeline_id == trow.id)
            ).all()
        )
        dom = _to_domain(trow, scenes, prow, patterns)
        from aicos.infrastructure.editorial_style_embedding.sql_editorial_style_embedding_repository import (
            SqlEditorialStyleEmbeddingRepository,
        )

        emb = SqlEditorialStyleEmbeddingRepository().get_by_creative_id(session, creative_id)
        if emb is not None:
            dom = replace(dom, style_embedding=emb)
        return dom

    def save(self, session: Session, timeline: CreativeTimeline) -> str:
        existing = session.scalars(
            select(CreativeTimelineRow).where(CreativeTimelineRow.creative_id == timeline.creative_id)
        ).first()
        if existing is not None:
            session.delete(existing)
            session.flush()
            logger.debug("replaced_creative_timeline creative_id=%s", timeline.creative_id)

        tid = str(uuid.uuid4())
        from aicos.application.editorial_pattern_engine.serialization import report_to_jsonable

        report_json = None
        if timeline.pattern_engine_report is not None:
            report_json = report_to_jsonable(timeline.pattern_engine_report)
        trow = CreativeTimelineRow(
            id=tid,
            creative_id=timeline.creative_id,
            audio_path=timeline.audio_path,
            final_video_path=timeline.final_video_path,
            dataset_version=timeline.dataset_version,
            pattern_engine_report_json=report_json,
        )
        session.add(trow)
        session.flush()

        for s in timeline.timeline_scenes:
            session.add(
                TimelineSceneRow(
                    id=str(uuid.uuid4()),
                    creative_timeline_id=tid,
                    scene_index=s.scene_index,
                    clip_id=s.clip_id,
                    start_time_sec=s.start_time,
                    end_time_sec=s.end_time,
                    duration_sec=s.duration,
                    transition_type=s.transition_type,
                    narrative_role=s.narrative_role,
                    motion_intensity=s.motion_intensity,
                    visual_energy=s.visual_energy,
                    camera_type=s.camera_type,
                    semantic_tags_json=list(s.semantic_tags),
                    emotion_tags_json=list(s.emotion_tags),
                )
            )

        sp = timeline.style_profile
        ss = timeline.style_signals
        session.add(
            CreativeStyleProfileRow(
                id=str(uuid.uuid4()),
                creative_timeline_id=tid,
                hook_intensity=sp.hook_intensity,
                average_pacing=sp.average_pacing,
                motion_density=sp.motion_density,
                transition_density=sp.transition_density,
                narrative_aggressiveness=sp.narrative_aggressiveness,
                visual_dynamism=sp.visual_dynamism,
                cinematic_style_tags_json=list(sp.cinematic_style_tags),
                pacing_score=ss.pacing_score,
                hook_strength=ss.hook_strength,
                emotional_curve_json=list(ss.emotional_curve),
            )
        )

        for p in timeline.editorial_patterns:
            session.add(
                EditorialPatternRow(
                    id=str(uuid.uuid4()),
                    creative_timeline_id=tid,
                    pattern_id=p.pattern_id,
                    pattern_type=p.pattern_type,
                    pattern_sequence_json=list(p.pattern_sequence),
                    frequency=p.frequency,
                    confidence_score=p.confidence_score,
                )
            )
        logger.debug("saved_creative_timeline id=%s scenes=%s", tid, len(timeline.timeline_scenes))
        return tid
