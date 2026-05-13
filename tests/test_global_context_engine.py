"""Tests del Global Context Engine (Fase 1)."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from aicos.application.context.global_context_service import GlobalContextService
from aicos.application.context.query_enrichment import build_global_query_enrichment
from aicos.application.context.rule_based_global_context_provider import (
    RuleBasedGlobalContextProvider,
    RuleBasedNarrativeInferenceProvider,
)
from aicos.database.db import Base, GlobalContextEmbeddingRow, GlobalContextEntityRow, GlobalContextRow, ProjectRow
from aicos.domain.context.enums import IndustryType, NarrativeArc
from aicos.models.schemas import GlobalContextSummary
from aicos.services.context_repository import domain_global_context_to_summary, persist_global_context
from aicos.services.global_context_factory import build_global_context_service


def test_automotive_topic_and_anchors() -> None:
    p = RuleBasedGlobalContextProvider()
    text = (
        "Los aditivos para motor reducen el desgaste. Si ves humo saliendo del capó, "
        "puede ser daño interno grave. Tu carro pierde rendimiento y aceite."
    )
    ctx = p.analyze(text, product_category="automotive", target_audience="drivers")
    assert ctx.industry == IndustryType.AUTOMOTIVE
    assert "engine" in ctx.topic.lower() or "motor" in ctx.topic.lower() or "automotive" in ctx.topic.lower()
    assert "concern" in ctx.dominant_emotion or ctx.dominant_emotion == "concern"
    assert any("humo" in a or "smoke" in a or "motor" in a or "engine" in a for a in ctx.semantic_anchors)


def test_automotive_problem_solution_arc() -> None:
    p = RuleBasedGlobalContextProvider()
    n = RuleBasedNarrativeInferenceProvider()
    text = "Tenemos un problema serio con el motor. La solución es este aditivo premium."
    ctx = n.infer_arc(text, p.analyze(text, product_category=None, target_audience=None))
    assert ctx.narrative_arc == NarrativeArc.PROBLEM_SOLUTION


def test_cosmetic_industry() -> None:
    p = RuleBasedGlobalContextProvider()
    text = "Esta crema hidrata tu piel y reduce arrugas visibles en pocas semanas."
    ctx = p.analyze(text, product_category="belleza", target_audience="mujeres 30+")
    assert ctx.industry == IndustryType.COSMETICS


def test_medical_industry() -> None:
    p = RuleBasedGlobalContextProvider()
    text = "El paciente presenta síntomas leves. Consulta con tu doctor antes de cambiar la dosis."
    ctx = p.analyze(text, product_category="salud", target_audience="adultos")
    assert ctx.industry == IndustryType.MEDICAL


def test_empty_transcript_flags() -> None:
    p = RuleBasedGlobalContextProvider()
    ctx = p.analyze("", product_category=None, target_audience=None)
    assert "empty_transcript" in ctx.validation.flags


def test_short_transcript_flag() -> None:
    p = RuleBasedGlobalContextProvider()
    ctx = p.analyze("hola", product_category=None, target_audience=None)
    assert "transcript_too_short" in ctx.validation.flags


def test_smoke_motor_scene_enrichment() -> None:
    """Humo + motor deben anclar contexto automotriz, no humo genérico aislado."""
    p = RuleBasedGlobalContextProvider()
    full = (
        "Hablamos de aditivos para motores diésel y gasolina. "
        "El humo constante indica daño mecánico y pérdida de aceite en el vehículo."
    )
    ctx = p.analyze(full, product_category=None, target_audience=None)
    enrich = build_global_query_enrichment(ctx) or ""
    assert "automotive" in enrich.lower() or IndustryType.AUTOMOTIVE.value in enrich
    assert "humo" in enrich.lower() or "smoke" in enrich.lower() or "motor" in enrich.lower()


def test_global_context_service_without_embedding() -> None:
    svc = GlobalContextService(
        analyzer=RuleBasedGlobalContextProvider(),
        narrative=RuleBasedNarrativeInferenceProvider(),
        embedding=None,
    )
    ctx, vec = svc.build_from_transcript(
        "motor humo aceite carro rendimiento",
        project_correlation_id=str(uuid.uuid4()),
        generate_embedding=False,
    )
    assert ctx.id
    assert vec is None


def test_domain_to_summary_roundtrip_json() -> None:
    svc = build_global_context_service(with_embedding=False)
    ctx, _vec = svc.build_from_transcript(
        "testimonio de cliente feliz con el producto",
        project_correlation_id=str(uuid.uuid4()),
        generate_embedding=False,
    )
    summary = domain_global_context_to_summary(ctx)
    data = summary.model_dump()
    back = GlobalContextSummary.model_validate(data)
    assert back.industry == summary.industry


def test_sqlite_persistence_memory() -> None:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    Sf = sessionmaker(engine, expire_on_commit=False, class_=Session)
    pid = str(uuid.uuid4())
    cid = str(uuid.uuid4())
    summary = GlobalContextSummary(
        topic="engine smoke",
        industry="automotive",
        semantic_entities=["engine", "smoke"],
        dominant_emotion="concern",
        narrative_arc="problem_solution",
        visual_style="mechanical_cinematic",
        semantic_anchors=["engine", "smoke", "oil"],
        content_intent="warn",
        cinematic_context="mechanical cinematic",
        product_context="additive",
        continuity_context="cohesive",
        validation_flags=[],
        transcript_fingerprint="abc",
        embedding_vector_id="e1",
    )
    vec = [0.1, 0.2, 0.3]
    with Sf() as session:
        session.add(ProjectRow(id=pid, name="t", status="draft"))
        session.flush()
        persist_global_context(session, project_id=pid, context_id=cid, summary=summary, embedding_vector=vec)
        session.commit()
    with Sf() as session:
        row = session.get(GlobalContextRow, cid)
        assert row is not None
        assert row.topic == "engine smoke"
        from sqlalchemy import select

        ents = session.scalars(
            select(GlobalContextEntityRow).where(GlobalContextEntityRow.global_context_id == cid)
        ).all()
        assert len(ents) >= 2
        emb = session.scalars(
            select(GlobalContextEmbeddingRow).where(GlobalContextEmbeddingRow.global_context_id == cid)
        ).one()
        assert emb.dimensions == 3


def test_build_query_text_prefixes_global_enrichment() -> None:
    from aicos.models.schemas import SearchRequest
    from aicos.modules.search_query_text import build_semantic_query_text

    req = SearchRequest(
        query="humo",
        narrative_function="PROBLEM",
        global_query_enrichment="automotive engine mechanical damage oil",
    )
    qtext = build_semantic_query_text(req)
    assert "automotive" in qtext
    assert "humo" in qtext or "problem" in qtext.lower()
