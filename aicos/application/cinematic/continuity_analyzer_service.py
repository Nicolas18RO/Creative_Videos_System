"""Continuidad temática / visual respecto a clips ya elegidos en la sesión."""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass

from aicos.models.schemas import Recommendation, SearchRankingContext

logger = logging.getLogger(__name__)


def _tok(s: str) -> set[str]:
    raw = re.sub(r"[^\w\sáéíóúñü]", " ", (s or "").lower(), flags=re.UNICODE)
    return {t for t in raw.split() if len(t) >= 3}


@dataclass(slots=True)
class ContinuityAnalyzerService:
    """Coherencia con escenas previas y anti-repetición de clip."""

    def score(self, rec: Recommendation, ctx: SearchRankingContext) -> float:
        t0 = time.perf_counter()
        if rec.clip_id in ctx.previous_selected_clip_ids:
            logger.info("[Continuity] clip=%s repeat_in_session=true score=0.15", rec.clip_id)
            return 0.15
        prior_blob = " ".join(ctx.prior_scene_concepts).lower()
        if not prior_blob.strip():
            out = 0.55
            logger.info("[Continuity] no_prior score=%.2f elapsed_ms=%.1f", out, (time.perf_counter() - t0) * 1000)
            return out
        c_blob = " ".join(
            filter(
                None,
                [
                    rec.clip_semantic_text or "",
                    rec.clip_subcategory or "",
                    rec.clip_context or "",
                    rec.clip_path or "",
                ],
            )
        ).lower()
        if not c_blob.strip():
            out = 0.48
            logger.info("[Continuity] empty_clip_blob score=%.2f", out)
            return out
        inter = len(_tok(prior_blob) & _tok(c_blob))
        union = len(_tok(prior_blob) | _tok(c_blob)) or 1
        j = inter / union
        out = max(0.25, min(0.95, 0.35 + 0.6 * j))
        logger.info(
            "[Continuity] clip=%s jaccard=%.3f score=%.3f elapsed_ms=%.1f",
            rec.clip_id,
            j,
            out,
            (time.perf_counter() - t0) * 1000,
        )
        return out
