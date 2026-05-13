"""Endpoints de decisiones del sistema (Fase 4), solo lectura con caché en servicio."""

from __future__ import annotations

from fastapi import APIRouter, Query

from aicos.database.db import session_scope
from aicos.models.schemas import DecisionsImpactResponse, DecisionsListResponse, DecisionsSummaryResponse
from aicos.services.decision_engine import build_decisions_impact, build_decisions_list, build_decisions_summary

router = APIRouter()


@router.get("/summary", response_model=DecisionsSummaryResponse)
def get_decisions_summary(
    refresh: bool = Query(False, description="Recalcula decisiones desde insights + SQLite."),
) -> DecisionsSummaryResponse:
    with session_scope() as session:
        return build_decisions_summary(session, refresh=refresh)


@router.get("/list", response_model=DecisionsListResponse)
def get_decisions_list(
    refresh: bool = Query(False, description="Si true, invalida caché y recalcula antes de paginar."),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    decision_type: str | None = Query(None, description="optimization | content | retrieval"),
    severity: str | None = Query(None, description="low | medium | high"),
) -> DecisionsListResponse:
    with session_scope() as session:
        return build_decisions_list(
            session,
            refresh=refresh,
            limit=limit,
            offset=offset,
            decision_type=decision_type,
            severity=severity,
        )


@router.get("/impact", response_model=DecisionsImpactResponse)
def get_decisions_impact(
    refresh: bool = Query(False, description="Si true, invalida caché y recalcula."),
) -> DecisionsImpactResponse:
    with session_scope() as session:
        return build_decisions_impact(session, refresh=refresh)
