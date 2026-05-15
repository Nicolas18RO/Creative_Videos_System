"""Factoría Fase 6.2 — adaptadores con sesión SQLite (sin lógica editorial)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from aicos.application.editorial_pattern_engine.editorial_pattern_extraction_engine import (
    EditorialPatternExtractionEngine,
)
from aicos.config import AppConfig, get_config
from aicos.infrastructure.editorial_pattern_engine.sql_clip_usage_digest_adapter import (
    SqlClipUsageHistoryDigestAdapter,
)
from aicos.infrastructure.editorial_pattern_engine.sql_timeline_enrichment_adapter import (
    SqlTimelinePatternEnrichmentAdapter,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def build_editorial_pattern_extraction_engine(
    session: Session | None,
    app_cfg: AppConfig | None = None,
) -> EditorialPatternExtractionEngine:
    cfg = app_cfg or get_config()
    eng = cfg.editorial_pattern_engine
    enrichment = SqlTimelinePatternEnrichmentAdapter(session) if session is not None else None
    usage = SqlClipUsageHistoryDigestAdapter(session) if session is not None else None
    return EditorialPatternExtractionEngine(
        dataset_cfg=cfg.editorial_dataset,
        engine_cfg=eng,
        enrichment=enrichment,
        usage_digest=usage,
    )
