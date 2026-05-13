"""Enriquecimiento híbrido textual + visual sobre candidatos ya rankeados (Fase 5.2)."""

from __future__ import annotations

import logging

from aicos.config import MultimodalRetrievalConfig
from aicos.domain.multimodal_retrieval.hybrid_scoring import compute_visual_similarity_components
from aicos.models.schemas import Recommendation, SearchRequest, SearchRunContext

logger = logging.getLogger(__name__)


def _reference_visual_signals(req: SearchRequest) -> tuple[str, str]:
    ref_fp = (req.reference_visual_fingerprint or "").strip()
    ref_cl = (req.reference_visual_cluster_id or "").strip()
    return ref_fp, ref_cl


def _continuity_style_score(clip_text: str | None, session_style: str) -> float:
    if not session_style or not clip_text:
        return 0.0
    a, b = session_style.lower(), clip_text.lower()
    if a in b or b in a:
        return 0.08
    return 0.0


def apply_multimodal_hybrid_to_recommendations(
    recs: list[Recommendation],
    req: SearchRequest,
    *,
    retrieval_cfg: MultimodalRetrievalConfig,
    context: SearchRunContext | None = None,
) -> list[Recommendation]:
    """Suma término visual (y continuidad débil) sin eliminar el score semántico previo."""
    if not retrieval_cfg.enabled or not retrieval_cfg.enable_visual_similarity or not recs:
        return recs
    ref_fp, ref_cluster = _reference_visual_signals(req)
    session_style = ""
    if context and context.global_context:
        session_style = (context.global_context.visual_style or "").strip()
    out: list[Recommendation] = []
    for r in recs:
        _, _, vis = compute_visual_similarity_components(
            reference_fingerprint=ref_fp,
            reference_cluster_id=ref_cluster,
            clip_fingerprint=r.cm_visual_embedding_fp,
            clip_cluster_id=r.cm_visual_cluster_id,
        )
        continuity = _continuity_style_score(r.clip_semantic_text, session_style)
        boost = retrieval_cfg.visual_similarity_weight * vis + continuity
        new_fs = max(0.0, min(1.0, float(r.final_score) + boost))
        logger.info(
            "[MultimodalRetrieval] clip=%s visual_similarity=%.4f continuity=%.4f",
            r.clip_id,
            vis,
            continuity,
        )
        logger.info(
            "[HybridVisualScore] clip=%s visual_score=%.4f final=%.4f",
            r.clip_id,
            vis,
            new_fs,
        )
        out.append(
            r.model_copy(
                update={
                    "final_score": new_fs,
                    "visual_similarity_score": vis,
                }
            )
        )
    out.sort(key=lambda x: (-x.final_score, x.clip_id))
    return out
