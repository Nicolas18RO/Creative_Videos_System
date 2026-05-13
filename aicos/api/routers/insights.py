"""Endpoints de insights (Fase 3): solo lectura, agregados con caché en servicio."""

from __future__ import annotations

from fastapi import APIRouter, Query

from aicos.database.db import session_scope
from aicos.models.schemas import InsightsGapsResponse, InsightsSummaryResponse, InsightsTrendsResponse
from aicos.services.insight_service import (
    build_insights_gaps,
    build_insights_summary,
    build_insights_trends,
    invalidate_insights_cache,
)

router = APIRouter()


@router.get("/summary", response_model=InsightsSummaryResponse)
def get_insights_summary(
    refresh: bool = Query(False, description="Si true, invalida caché y recalcula agregados."),
) -> InsightsSummaryResponse:
    if refresh:
        invalidate_insights_cache()
    with session_scope() as session:
        return build_insights_summary(session, refresh=refresh)


@router.get("/gaps", response_model=InsightsGapsResponse)
def get_insights_gaps(
    refresh: bool = Query(False, description="Si true, invalida caché y recalcula agregados."),
) -> InsightsGapsResponse:
    if refresh:
        invalidate_insights_cache()
    with session_scope() as session:
        return build_insights_gaps(session, refresh=refresh)


@router.get("/trends", response_model=InsightsTrendsResponse)
def get_insights_trends(
    refresh: bool = Query(False, description="Si true, invalida caché y recalcula agregados."),
) -> InsightsTrendsResponse:
    if refresh:
        invalidate_insights_cache()
    with session_scope() as session:
        return build_insights_trends(session, refresh=refresh)
