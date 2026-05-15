"""Orquestación: digest textual + vector estructural + fusión (Fase 6.3)."""

from __future__ import annotations

import logging
import math
from typing import Any

from aicos.application.editorial_style_embedding.ports import SemanticStyleEmbeddingPort
from aicos.application.editorial_style_embedding.style_structural_source_builder import build_style_structural_source
from aicos.config import EditorialStyleEmbeddingConfig, get_config
from aicos.domain.editorial_dataset.entities import CreativeTimeline
from aicos.domain.editorial_style_embedding.digest_builder import (
    build_editorial_style_digest_text,
    sha256_hex,
    summarize_patterns_for_digest,
)
from aicos.domain.editorial_style_embedding.entities import EditorialStyleEmbedding
from aicos.domain.editorial_style_embedding.structural_vector import structural_vector_from_source

logger = logging.getLogger(__name__)


def _l2_normalize(vec: tuple[float, ...]) -> tuple[float, ...]:
    n = math.sqrt(sum(x * x for x in vec)) or 1.0
    return tuple(float(x / n) for x in vec)


def _fuse_vectors(
    structural: tuple[float, ...],
    semantic: tuple[float, ...] | None,
    *,
    max_fused_dim: int,
    mode: str,
) -> tuple[float, ...]:
    if semantic is None or mode == "structural_only":
        return structural
    if mode == "concat_l2":
        merged = list(structural) + list(semantic)
        if len(merged) > max_fused_dim:
            merged = merged[:max_fused_dim]
        return _l2_normalize(tuple(merged))
    if mode == "concat_raw":
        merged = list(structural) + list(semantic)
        return tuple(float(x) for x in merged[:max_fused_dim])
    return structural


class EditorialStyleEmbeddingService:
    """Transforma timeline + informe 6.2 en embeddings editoriales reutilizables."""

    def __init__(
        self,
        cfg: EditorialStyleEmbeddingConfig,
        semantic: SemanticStyleEmbeddingPort | None,
    ) -> None:
        self._cfg = cfg
        self._semantic = semantic

    def embed_timeline(
        self,
        timeline: CreativeTimeline,
        *,
        pattern_engine_report: Any | None = None,
    ) -> EditorialStyleEmbedding:
        if not self._cfg.enabled:
            raise RuntimeError("editorial_style_embedding_disabled")

        src = build_style_structural_source(timeline, pattern_engine_report)
        structural = structural_vector_from_source(src)
        structural_tag = self._cfg.structural_model_tag

        sp = timeline.style_profile
        ss = timeline.style_signals
        scenes = timeline.timeline_scenes
        duration = max((s.end_time for s in scenes), default=0.0)
        hooks = timeline.hook_detection
        hook_txt = ""
        if hooks:
            hook_txt = f"strength={hooks[0].hook_strength:.2f};" + ",".join(hooks[0].reasons)
        rhythm_txt = (
            f"cpm={src.cuts_per_minute:.1f};mean_shot={src.cut_mean_shot_sec:.2f}s;"
            f"cv={src.cut_cv:.2f};bursts={src.burst_window_count}"
        )
        nar_txt = f"conf={src.narrative_phase_confidence:.2f};bucket={src.narrative_structure_bucket}"
        usage_txt = (
            f"src_entropy={src.usage_source_entropy:.2f};cluster_streak={src.usage_max_cluster_streak_norm:.2f};"
            f"pressure={src.usage_pressure_mean_norm:.2f}"
        )
        patterns = (
            summarize_patterns_for_digest(pattern_engine_report.sequence_patterns)
            if pattern_engine_report is not None
            else summarize_patterns_for_digest(timeline.editorial_patterns)
        )
        digest = build_editorial_style_digest_text(
            creative_id=timeline.creative_id,
            scene_count=len(scenes),
            total_duration_sec=float(duration),
            style_tags=sp.cinematic_style_tags,
            pattern_summaries=patterns,
            signature_tags=src.signature_tags,
            overlay_tags=src.cinematic_overlay_tags,
            hook_summary=hook_txt,
            rhythm_summary=rhythm_txt,
            narrative_summary=nar_txt,
            usage_summary=usage_txt,
        )
        digest_hash = sha256_hex(digest)

        semantic_vec: tuple[float, ...] | None = None
        sem_tag: str | None = None
        if self._cfg.enable_semantic_embedding and self._semantic is not None:
            try:
                semantic_vec = self._semantic.embed_digest(digest[: self._cfg.digest_max_chars])
                sem_tag = (self._cfg.semantic_model_tag or "").strip() or get_config().embeddings.model
            except Exception as e:
                logger.warning("[StyleEmbedding] semantic_embed_failed creative=%s err=%s", timeline.creative_id, e)

        fused = _fuse_vectors(
            structural,
            semantic_vec,
            max_fused_dim=self._cfg.max_fused_dimension,
            mode=self._cfg.fusion_mode,
        )
        logger.info(
            "[StyleEmbedding] creative=%s struct_dim=%s sem_dim=%s fused_dim=%s",
            timeline.creative_id,
            len(structural),
            len(semantic_vec) if semantic_vec else 0,
            len(fused),
        )
        return EditorialStyleEmbedding(
            creative_id=timeline.creative_id,
            structural_vector=structural,
            semantic_vector=semantic_vec,
            fused_vector=fused,
            digest_text=digest[: self._cfg.digest_max_chars],
            digest_sha256=digest_hash,
            structural_model_tag=structural_tag,
            semantic_model_tag=sem_tag,
            fusion_mode=self._cfg.fusion_mode,
        )
