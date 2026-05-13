"""Persistencia de proyectos, escenas, recomendaciones y gaps (SQLite)."""

from __future__ import annotations

import logging
import uuid

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from aicos.config import get_config
from aicos.database.db import ClipRow, GapRow, ProjectRow, RecommendationRow, SceneRow
from aicos.models.schemas import (
    AnalyzeAPIResponse,
    Gap,
    GapListItem,
    ProjectDetailResponse,
    ProjectGapsResponse,
    ProjectSummary,
    RecommendationDetail,
    SceneDetailOut,
)

logger = logging.getLogger(__name__)


def _write_transcript(project_id: str, analysis: AnalyzeAPIResponse) -> str | None:
    paths = get_config().resolved_paths()
    exports = paths["exports"]
    exports.mkdir(parents=True, exist_ok=True)
    out = exports / f"{project_id}_transcript.json"
    try:
        out.write_text(
            analysis.transcript.model_dump_json(indent=2),
            encoding="utf-8",
        )
        return str(out)
    except OSError as e:
        logger.warning("No se pudo escribir transcript: %s", e)
        return None


def persist_full_analysis(
    session: Session,
    analysis: AnalyzeAPIResponse,
    *,
    audio_path: str,
    product_name: str | None = None,
    product_category: str | None = None,
    target_audience: str | None = None,
) -> None:
    """Guarda proyecto, escenas, recomendaciones y gaps asociados al análisis.

    Orden garantizado por escena: ``SceneRow`` → ``flush`` → recomendaciones → ``flush`` →
    ``GapRow`` (savepoint) para no abortar todo el análisis si un gap viola FK.
    """
    pid = analysis.project_id
    session.execute(delete(ProjectRow).where(ProjectRow.id == pid))

    tpath = _write_transcript(pid, analysis)
    proj = ProjectRow(
        id=pid,
        name=analysis.project_name,
        product_name=product_name,
        product_category=product_category,
        target_audience=target_audience,
        audio_file_path=audio_path,
        transcript_path=tpath,
        status="in_progress",
    )
    session.add(proj)
    session.flush()
    logger.info("[Persistence] project_id=%s name=%r rows flushed", pid, analysis.project_name)

    if analysis.global_context_id and analysis.global_context is not None:
        from aicos.services import context_repository

        context_repository.persist_global_context(
            session,
            project_id=pid,
            context_id=analysis.global_context_id,
            summary=analysis.global_context,
            embedding_vector=analysis.global_context_embedding_vector,
        )
        session.flush()

    for block in analysis.scenes:
        sc = block.scene
        session.add(
            SceneRow(
                id=sc.scene_id,
                project_id=pid,
                scene_index=sc.scene_index,
                start_ms=sc.start_ms,
                end_ms=sc.end_ms,
                duration_ms=sc.duration_ms,
                text=sc.text,
                concept=sc.concept,
                narrative_function=sc.narrative_function,
                is_hook=sc.is_hook,
                hook_score=sc.hook_score,
                gender_hint=sc.gender_hint,
                selected_clip_id=block.recommendations[0].clip_id if block.recommendations else None,
                gap_detected=block.is_gap,
                global_context_id=sc.global_context_id,
            )
        )
        session.flush()
        logger.info(
            "[Persistence] inserting scenes project_id=%s scene_id=%s index=%s",
            pid,
            sc.scene_id,
            sc.scene_index,
        )

        for rec in block.recommendations:
            session.add(
                RecommendationRow(
                    id=str(uuid.uuid4()),
                    scene_id=sc.scene_id,
                    clip_id=rec.clip_id,
                    similarity_score=rec.similarity_score,
                    taxonomy_boost=rec.taxonomy_boost,
                    final_score=rec.final_score,
                    rank=rec.rank,
                    accepted=None,
                )
            )
        session.flush()
        logger.info(
            "[Persistence] inserting recommendations scene_id=%s count=%s",
            sc.scene_id,
            len(block.recommendations),
        )

        if block.gap is not None:
            g = block.gap
            if g.scene_id != sc.scene_id:
                logger.error(
                    "[Persistence] gap scene_id mismatch (skip): gap.scene_id=%s scene.scene_id=%s",
                    g.scene_id,
                    sc.scene_id,
                )
            elif session.get(SceneRow, sc.scene_id) is None:
                logger.error("[Persistence] gap skip: SceneRow no encontrada id=%s", sc.scene_id)
            else:
                try:
                    with session.begin_nested():
                        session.add(
                            GapRow(
                                id=str(uuid.uuid4()),
                                scene_id=sc.scene_id,
                                concept=g.concept,
                                narrative_function=g.narrative_function,
                                gap_type=g.gap_type,
                                tiktok_keywords=g.tiktok_keywords,
                                ai_image_prompt=g.ai_image_prompt,
                                ai_motion_prompt=g.ai_motion_prompt,
                                taxonomy_suggestion=g.taxonomy_suggestion,
                                resolution_type=None,
                            )
                        )
                        session.flush()
                    logger.info("[Persistence] inserting gaps scene_id=%s ok", sc.scene_id)
                except IntegrityError:
                    logger.exception(
                        "[Persistence] inserting gaps FAILED scene_id=%s project_id=%s",
                        sc.scene_id,
                        pid,
                    )

    session.flush()


def update_recommendation_feedback(
    session: Session,
    *,
    scene_id: str,
    clip_id: str,
    accepted: bool,
    rank: int | None = None,
) -> int:
    """Actualiza `accepted` en recomendaciones que coincidan con escena + clip.

    Returns:
        Número de filas actualizadas (0 si no hubo coincidencias).
    """
    stmt = select(RecommendationRow).where(
        RecommendationRow.scene_id == scene_id,
        RecommendationRow.clip_id == clip_id,
    )
    if rank is not None:
        stmt = stmt.where(RecommendationRow.rank == rank)
    rows = list(session.scalars(stmt).all())
    for r in rows:
        r.accepted = accepted
    scene = session.get(SceneRow, scene_id)
    if scene is not None:
        if accepted:
            scene.selected_clip_id = clip_id
            clip_row = session.get(ClipRow, clip_id)
            if clip_row is not None:
                clip_row.times_used = int(clip_row.times_used or 0) + 1
        elif not accepted and scene.selected_clip_id == clip_id:
            scene.selected_clip_id = None
    session.flush()
    return len(rows)


def list_projects(session: Session) -> list[ProjectSummary]:
    """Lista proyectos persistidos (más recientes primero)."""
    rows = session.scalars(select(ProjectRow).order_by(ProjectRow.created_at.desc())).all()
    out: list[ProjectSummary] = []
    for r in rows:
        created = r.created_at.isoformat() if getattr(r, "created_at", None) else None
        out.append(
            ProjectSummary(
                id=r.id,
                name=r.name,
                status=r.status or "draft",
                audio_file_path=r.audio_file_path,
                created_at=created,
            )
        )
    return out


def get_project_detail(session: Session, project_id: str) -> ProjectDetailResponse | None:
    """Detalle de proyecto con escenas y recomendaciones enriquecidas con `clips`."""
    proj = session.get(ProjectRow, project_id)
    if proj is None:
        return None
    created = proj.created_at.isoformat() if getattr(proj, "created_at", None) else None
    summary = ProjectSummary(
        id=proj.id,
        name=proj.name,
        status=proj.status or "draft",
        audio_file_path=proj.audio_file_path,
        created_at=created,
    )
    scene_rows = session.scalars(
        select(SceneRow)
        .where(SceneRow.project_id == project_id)
        .order_by(SceneRow.scene_index)
    ).all()
    scenes_out: list[SceneDetailOut] = []
    for sc in scene_rows:
        rec_rows = session.scalars(
            select(RecommendationRow)
            .where(RecommendationRow.scene_id == sc.id)
            .order_by(RecommendationRow.rank)
        ).all()
        rec_out: list[RecommendationDetail] = []
        for rec in rec_rows:
            clip = session.get(ClipRow, rec.clip_id)
            clip_path = clip.absolute_path if clip else ""
            thumb = clip.thumbnail_path if clip else None
            rec_out.append(
                RecommendationDetail(
                    id=rec.id,
                    clip_id=rec.clip_id,
                    clip_path=clip_path or "",
                    rank=rec.rank,
                    similarity_score=rec.similarity_score,
                    final_score=rec.final_score,
                    accepted=rec.accepted,
                    thumbnail_path=thumb,
                )
            )
        scenes_out.append(
            SceneDetailOut(
                scene_id=sc.id,
                scene_index=sc.scene_index,
                text=sc.text,
                concept=sc.concept,
                narrative_function=sc.narrative_function,
                is_hook=bool(sc.is_hook),
                gender_hint=sc.gender_hint,
                recommendations=rec_out,
            )
        )
    return ProjectDetailResponse(project=summary, scenes=scenes_out)


def get_project_gaps(session: Session, project_id: str) -> ProjectGapsResponse:
    """Lista gaps persistidos para un proyecto."""
    row = session.get(ProjectRow, project_id)
    if row is None:
        return ProjectGapsResponse(project_id=project_id, project_name=None, gaps=[])

    stmt = (
        select(GapRow, SceneRow.scene_index)
        .join(SceneRow, GapRow.scene_id == SceneRow.id)
        .where(SceneRow.project_id == project_id)
        .order_by(SceneRow.scene_index)
    )
    items: list[GapListItem] = []
    for gap_row, scene_index in session.execute(stmt).all():
        g = Gap.model_validate(
            {
                "scene_id": gap_row.scene_id,
                "concept": gap_row.concept,
                "narrative_function": gap_row.narrative_function,
                "gap_type": gap_row.gap_type,
                "tiktok_keywords": list(gap_row.tiktok_keywords or []),
                "ai_image_prompt": gap_row.ai_image_prompt,
                "ai_motion_prompt": gap_row.ai_motion_prompt,
                "taxonomy_suggestion": gap_row.taxonomy_suggestion or "",
            }
        )
        items.append(GapListItem(scene_index=scene_index, gap=g))
    return ProjectGapsResponse(project_id=project_id, project_name=row.name, gaps=items)
