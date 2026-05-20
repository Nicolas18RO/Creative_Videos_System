"""Rutas REST Fase 6.7.1 — registry de sesiones en dataset editorial."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from aicos.application.editorial_registry.presentation import session_to_out, summary_to_out
from aicos.config import get_config
from aicos.database.db import session_scope
from aicos.models.schemas import (
    EditorialRegistryDuplicateCheckResponse,
    EditorialRegistryListResponse,
    EditorialRegistrySummaryOut,
)
from aicos.services.editorial_registry_factory import build_editorial_registry_service

router = APIRouter()


def _require_registry() -> None:
    cfg = get_config()
    if not cfg.editorial_registry.enabled:
        raise HTTPException(status_code=404, detail="editorial_registry_disabled")
    if not cfg.editorial_training_workspace.enabled:
        raise HTTPException(status_code=404, detail="editorial_training_workspace_disabled")


@router.get("/sessions", response_model=EditorialRegistryListResponse)
def list_registry_sessions(
    status: str | None = Query(default=None, max_length=32),
    product_category: str | None = Query(default=None, max_length=256),
) -> EditorialRegistryListResponse:
    _require_registry()
    svc = build_editorial_registry_service()
    with session_scope() as session:
        rows = svc.list_sessions(session, status=status, product_category=product_category)
        summary = svc.get_summary(session)
    return EditorialRegistryListResponse(
        sessions=[session_to_out(r) for r in rows],
        summary=summary_to_out(summary),
    )


@router.get("/summary", response_model=EditorialRegistrySummaryOut)
def get_registry_summary() -> EditorialRegistrySummaryOut:
    _require_registry()
    svc = build_editorial_registry_service()
    with session_scope() as session:
        summary = svc.get_summary(session)
    return summary_to_out(summary)


@router.get("/duplicates-check", response_model=EditorialRegistryDuplicateCheckResponse)
def check_registry_duplicates(
    creative_id: str = Query(default="", max_length=128),
    creative_label: str = Query(default="", max_length=512),
) -> EditorialRegistryDuplicateCheckResponse:
    _require_registry()
    svc = build_editorial_registry_service()
    with session_scope() as session:
        dupes = svc.check_duplicates(session, creative_id=creative_id, creative_label=creative_label)
    out = [session_to_out(d) for d in dupes]
    return EditorialRegistryDuplicateCheckResponse(possible_duplicates=out, duplicate_count=len(out))
