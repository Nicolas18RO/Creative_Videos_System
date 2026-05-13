"""Repositorio SQLite para contexto global (solo mapeo ORM, sin reglas de negocio)."""

from __future__ import annotations

import logging
import uuid

from sqlalchemy.orm import Session

from aicos.database.db import GlobalContextEmbeddingRow, GlobalContextEntityRow, GlobalContextRow
from aicos.domain.context.entities import GlobalContext
from aicos.models.schemas import GlobalContextSummary

logger = logging.getLogger(__name__)


def domain_global_context_to_summary(ctx: GlobalContext) -> GlobalContextSummary:
    """Traduce entidad de dominio a contrato Pydantic de API."""
    return GlobalContextSummary(
        topic=ctx.topic,
        industry=ctx.industry.value,
        semantic_entities=list(ctx.semantic_entities),
        dominant_emotion=ctx.dominant_emotion,
        narrative_arc=ctx.narrative_arc.value,
        visual_style=ctx.visual_style.value,
        semantic_anchors=list(ctx.semantic_anchors),
        content_intent=ctx.content_intent.value,
        cinematic_context=ctx.cinematic_context,
        product_context=ctx.product_context,
        continuity_context=ctx.continuity_context,
        validation_flags=sorted(ctx.validation.flags),
        validation_notes=ctx.validation.notes,
        secondary_industries=[x.value for x in ctx.secondary_industries],
        embedding_vector_id=ctx.embedding_vector_id,
        transcript_fingerprint=ctx.transcript_fingerprint,
    )


def persist_global_context(
    session: Session,
    *,
    project_id: str,
    context_id: str,
    summary: GlobalContextSummary,
    embedding_vector: list[float] | None,
) -> None:
    """Inserta filas en ``global_contexts``, entidades y embedding (transacción externa)."""
    session.add(
        GlobalContextRow(
            id=context_id,
            project_id=project_id,
            transcript_fingerprint=summary.transcript_fingerprint or "",
            topic=summary.topic,
            industry=summary.industry,
            dominant_emotion=summary.dominant_emotion,
            narrative_arc=summary.narrative_arc,
            visual_style=summary.visual_style,
            content_intent=summary.content_intent,
            cinematic_context=summary.cinematic_context,
            product_context=summary.product_context,
            continuity_context=summary.continuity_context,
            semantic_entities_json=list(summary.semantic_entities),
            semantic_anchors_json=list(summary.semantic_anchors),
            secondary_industries_json=list(summary.secondary_industries),
            flags_json=list(summary.validation_flags),
            validation_notes=summary.validation_notes or None,
            embedding_vector_id=summary.embedding_vector_id,
            provider="rules",
        )
    )
    session.flush()
    seen: set[str] = set()
    for lab in summary.semantic_entities:
        k = lab.lower().strip()
        if not k or k in seen:
            continue
        seen.add(k)
        session.add(
            GlobalContextEntityRow(
                id=str(uuid.uuid4()),
                global_context_id=context_id,
                label=lab[:256],
                kind="semantic_entity",
                weight=1.0,
            )
        )
    for lab in summary.semantic_anchors:
        k = lab.lower().strip()
        if not k or k in seen:
            continue
        seen.add(k)
        session.add(
            GlobalContextEntityRow(
                id=str(uuid.uuid4()),
                global_context_id=context_id,
                label=lab[:256],
                kind="anchor",
                weight=1.05,
            )
        )
    session.flush()
    if embedding_vector:
        session.add(
            GlobalContextEmbeddingRow(
                id=str(uuid.uuid4()),
                global_context_id=context_id,
                provider="local",
                model_hint=None,
                dimensions=len(embedding_vector),
                vector_json=embedding_vector,
            )
        )
        session.flush()
    logger.info(
        "[Persistence] global_context id=%s project_id=%s anchors=%d has_vector=%s",
        context_id,
        project_id,
        len(summary.semantic_anchors),
        bool(embedding_vector),
    )
