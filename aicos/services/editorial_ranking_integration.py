"""Integración retrieval: boosts desde metadata editorial (Fase 5.3)."""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from aicos.config import EditorialMetadataConfig
from aicos.domain.editorial_metadata.rules import (
    calculate_editorial_quality_score,
    normalize_editorial_tags,
)
from aicos.infrastructure.editorial_metadata.sql_editorial_metadata_repository import (
    SqlEditorialMetadataRepository,
)
from aicos.models.schemas import Recommendation, SearchRequest

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def _query_tokens(q: str) -> set[str]:
    raw = re.sub(r"[^\w\sáéíóúñü]", " ", (q or "").lower(), flags=re.UNICODE)
    return {t for t in raw.split() if len(t) > 2}


def _tag_overlap_boost(query: str, tags: str | None) -> float:
    if not tags or not query:
        return 0.0
    qt = _query_tokens(query)
    if not qt:
        return 0.0
    norm = normalize_editorial_tags(tags)
    tt = set(norm.split(",")) if norm else set()
    overlap = len(qt & tt)
    if overlap == 0:
        return 0.0
    return min(0.05, 0.012 * overlap)


def apply_editorial_boosts_to_recommendations(
    session: "Session",
    recs: list[Recommendation],
    req: SearchRequest,
    *,
    editorial_cfg: EditorialMetadataConfig,
) -> list[Recommendation]:
    """Aplica pesos editoriales y refleja override de cluster en metadatos expuestos."""
    if not editorial_cfg.enabled or not editorial_cfg.enable_editorial_boosts or not recs:
        return recs
    repo = SqlEditorialMetadataRepository()
    facets = repo.fetch_editorial_rank_facets(session, [r.clip_id for r in recs])
    out: list[Recommendation] = []
    for r in recs:
        fac = facets.get(r.clip_id)
        qc = cc = ov = tags = None
        if fac is not None:
            qc, cc, ov, tags = fac
        qv = 0.0 if qc is None else max(0.0, min(1.0, float(qc)))
        cv = 0.0 if cc is None else max(0.0, min(1.0, float(cc)))
        boost = 0.0
        if qc is not None:
            boost += float(editorial_cfg.editorial_quality_weight) * qv
        if cc is not None:
            boost += float(editorial_cfg.cinematic_score_weight) * cv
        boost += _tag_overlap_boost(req.query, tags)
        new_fs = max(0.0, min(1.0, float(r.final_score) + boost))
        cm_cluster = r.cm_visual_cluster_id
        if ov and (ov or "").strip():
            cm_cluster = (ov or "").strip()
            logger.info("[EditorialOverride] cluster_override=%s clip=%s", ov, r.clip_id)
        combined = calculate_editorial_quality_score(
            quality_score=qc,
            cinematic_score=cc,
            quality_weight=editorial_cfg.editorial_quality_weight,
            cinematic_weight=editorial_cfg.cinematic_score_weight,
        )
        logger.info(
            "[EditorialQuality] clip=%s cinematic_score=%s quality_score=%s combined=%.3f",
            r.clip_id,
            cc,
            qc,
            combined,
        )
        out.append(
            r.model_copy(
                update={
                    "final_score": new_fs,
                    "cm_visual_cluster_id": cm_cluster,
                    "em_quality_score": qc,
                    "em_cinematic_score": cc,
                    "em_editorial_tags": tags,
                }
            )
        )
    out.sort(key=lambda x: (-x.final_score, x.clip_id))
    return out
