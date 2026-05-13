"""Servicio de aplicación: penalizaciones de reutilización y diversidad cinematográfica."""

from __future__ import annotations

import logging
from collections import Counter
from typing import Any

from aicos.application.cinematic_metadata.resolver import CinematicMetadataResolver
from aicos.application.clip_usage.signals_lexical import (
    compute_visual_diversity_signals,
    narrative_concept_overlap_penalty,
)
from aicos.config import ClipUsageIntelligenceConfig, get_config
from aicos.domain.clip_usage.derivations import infer_temporal_shot_bucket
from aicos.domain.clip_usage.entities import ClipReusePolicy
from aicos.models.schemas import Recommendation, SearchRequest, SearchRunContext
from aicos.services.cinematic_metadata_read_factory import create_cinematic_metadata_read_port

logger = logging.getLogger(__name__)


def _clip_blob(r: Recommendation) -> str:
    parts = [
        r.clip_semantic_text or "",
        r.clip_subcategory or "",
        r.clip_context or "",
        r.clip_path or "",
        r.narrative_function or "",
    ]
    return " ".join(parts).lower()


class ClipUsageIntelligenceService:
    """Continuity-aware diversity: penaliza repetición exacta, de origen y de cluster visual."""

    def __init__(self, cfg: ClipUsageIntelligenceConfig) -> None:
        self.cfg = cfg
        self._policy = ClipReusePolicy(
            allow_same_clip=cfg.allow_same_clip,
            allow_same_source_video=cfg.allow_same_source_video,
            allow_same_visual_cluster=cfg.allow_same_visual_cluster,
            max_reuse_penalty=min(1.0, max(0.0, cfg.max_reuse_penalty_cap)),
        )

    def apply_for_search(
        self,
        recs: list[Recommendation],
        req: SearchRequest,
        context: SearchRunContext,
        db_session: Any | None = None,
    ) -> list[Recommendation]:
        if not self.cfg.enabled or not recs:
            return recs
        if context.source != "audio" or context.scene_index is None:
            return recs

        records = list(context.clip_usage_records or [])
        used_ids = set(req.used_clip_ids)
        for rec in records:
            used_ids.add(rec.clip_id)

        source_counts = Counter(r.source_video_id for r in records if r.source_video_id)
        cluster_counts = Counter(r.visual_cluster_id for r in records if r.visual_cluster_id)
        last_fp = ""
        if records:
            last_fp = (records[-1].clip_fingerprint or "").strip()

        prior_concepts = []
        if context.ranking_context and context.ranking_context.prior_scene_concepts:
            prior_concepts = list(context.ranking_context.prior_scene_concepts)

        recent_buckets: list[str] = []
        for r in records[-3:]:
            fp = (r.clip_fingerprint or "").strip()
            if fp:
                recent_buckets.append(infer_temporal_shot_bucket(fp))

        min_alt = max(1, self.cfg.min_alternatives_for_hard_exclude)

        store = create_cinematic_metadata_read_port(db_session)
        resolver = CinematicMetadataResolver(store)

        scored: list[tuple[Recommendation, float, dict[str, float]]] = []
        for r in recs:
            blob = _clip_blob(r)
            src = resolver.resolve_source_video_id(r)
            cluster = resolver.resolve_visual_cluster_id(r)

            reused = r.clip_id in used_ids
            logger.info("[ClipUsage] clip=%s reused=%s", r.clip_id, reused)

            reuse_pen = 0.0
            if reused:
                reuse_pen = float(self.cfg.exact_clip_penalty)
                logger.info("[ReusePenalty] clip=%s penalty=%.4f", r.clip_id, reuse_pen)

            src_uses = source_counts.get(src, 0)
            src_pen = 0.0
            if src_uses > 0 and not self._policy.allow_same_source_video:
                src_pen = float(self.cfg.same_source_penalty) * min(2.0, 0.5 + src_uses * 0.35)
            elif src_uses > 0:
                src_pen = float(self.cfg.same_source_penalty) * min(1.5, src_uses * 0.45)

            cl_uses = cluster_counts.get(cluster, 0)
            cluster_pen = 0.0
            if cl_uses > 0 and not self._policy.allow_same_visual_cluster:
                cluster_pen = float(self.cfg.same_cluster_penalty) * min(2.0, 0.55 + cl_uses * 0.3)
            elif cl_uses > 0:
                cluster_pen = float(self.cfg.same_cluster_penalty) * min(1.5, cl_uses * 0.4)

            vis_pen = 0.0
            cluster_overlap = 0.0
            if last_fp:
                sig = compute_visual_diversity_signals(blob, last_fp)
                cluster_overlap = (
                    sig.color_similarity
                    + sig.shot_similarity
                    + sig.motion_similarity
                    + sig.composition_similarity
                    + sig.semantic_similarity
                ) / 5.0
                vis_pen = float(self.cfg.same_cluster_penalty) * 0.55 * cluster_overlap
                logger.info(
                    "[VisualDiversity] clip=%s cluster_overlap=%.4f redundancy_penalty=%.4f",
                    r.clip_id,
                    cluster_overlap,
                    vis_pen,
                )

            narr_pen = narrative_concept_overlap_penalty(
                blob,
                prior_concepts,
                scale=float(self.cfg.narrative_overlap_penalty_scale),
            )

            cur_bucket = infer_temporal_shot_bucket(blob)
            temporal_pen = 0.0
            if recent_buckets and cur_bucket != "general":
                streak = sum(1 for b in reversed(recent_buckets) if b == cur_bucket)
                if streak >= 1:
                    temporal_pen = float(self.cfg.temporal_repeat_penalty) * min(2.0, streak + 0.5)

            div_stack = reuse_pen + src_pen + cluster_pen + vis_pen + narr_pen + temporal_pen
            w_div = float(self.cfg.diversity_weight)
            w_cont = float(self.cfg.continuity_weight)
            continuity_aware = w_div * div_stack + w_cont * temporal_pen
            base = float(r.final_score)
            new_final = max(0.0, min(1.0, base - continuity_aware))

            meta = {
                "reuse_penalty": reuse_pen,
                "source_penalty": src_pen,
                "cluster_penalty": cluster_pen,
                "visual_redundancy_penalty": vis_pen,
                "narrative_overlap_penalty": narr_pen,
                "temporal_penalty": temporal_pen,
            }
            scored.append((r, new_final, meta))

        scored.sort(key=lambda x: (-x[1], x[0].clip_id))

        filtered = scored
        if self.cfg.hard_exclude_exact_reuse and not self._policy.allow_same_clip:
            blocked = set(used_ids)
            feasible = [t for t in scored if t[0].clip_id not in blocked]
            if len(feasible) >= min_alt:
                filtered = feasible
                logger.info(
                    "[ClipUsage] hard_exclude_exact=true removed=%d kept=%d",
                    len(scored) - len(feasible),
                    len(feasible),
                )
            else:
                logger.info(
                    "[ClipUsage] hard_exclude_relaxed=true pool=%d min_alt=%d",
                    len(scored),
                    min_alt,
                )

        out: list[Recommendation] = []
        for r, fs, _meta in filtered:
            out.append(r.model_copy(update={"final_score": fs}))

        if not out:
            out = [t[0].model_copy(update={"final_score": t[1]}) for t in scored[: req.n_results]]

        out.sort(key=lambda x: (-x.final_score, x.clip_id))

        if out:
            top = out[0]
            top_meta = next((m for r, _, m in filtered if r.clip_id == top.clip_id), {})
            div_score = max(0.0, 1.0 - min(1.0, float(top_meta.get("visual_redundancy_penalty", 0.0)) * 2.0))
            logger.info(
                "[CUI_FinalSelection] scene=%s selected_clip=%s diversity_score=%.4f final_score=%.4f",
                context.scene_index,
                top.clip_id,
                div_score,
                float(top.final_score),
            )

        return out


def get_clip_usage_intelligence_service() -> ClipUsageIntelligenceService:
    try:
        cfg = get_config().clip_usage_intelligence
    except Exception as e:
        logger.warning("[ClipUsage] get_config_fallback defaults: %s", e)
        cfg = ClipUsageIntelligenceConfig()
    return ClipUsageIntelligenceService(cfg)
