"""Caso de uso: construir contexto global desde transcript completo."""

from __future__ import annotations

import hashlib
import logging
import time
import uuid
from dataclasses import replace

from aicos.application.context.ports import (
    ContextAnalyzerPort,
    GlobalEmbeddingPort,
    NarrativeInferencePort,
)
from aicos.domain.context.entities import GlobalContext, GlobalContextValidation

logger = logging.getLogger(__name__)


class GlobalContextService:
    """Orquesta análisis, inferencia narrativa y embedding global (local-first)."""

    def __init__(
        self,
        analyzer: ContextAnalyzerPort,
        narrative: NarrativeInferencePort,
        embedding: GlobalEmbeddingPort | None = None,
    ) -> None:
        self._analyzer = analyzer
        self._narrative = narrative
        self._embedding = embedding

    def build_from_transcript(
        self,
        transcript_text: str,
        *,
        project_correlation_id: str,
        product_category: str | None = None,
        target_audience: str | None = None,
        generate_embedding: bool = True,
    ) -> tuple[GlobalContext, list[float] | None]:
        """Genera contexto global listo para asociar a escenas y persistir con el proyecto."""
        t0 = time.perf_counter()
        logger.info("[GlobalContext] start project_correlation_id=%s", project_correlation_id)
        stripped = (transcript_text or "").strip()
        extra_flags: set[str] = set()
        if not stripped:
            extra_flags.add("empty_transcript")
        ctx0 = self._analyzer.analyze(
            stripped,
            product_category=product_category,
            target_audience=target_audience,
        )
        ctx1 = self._narrative.infer_arc(stripped, ctx0)
        merged_flags = frozenset(set(ctx1.validation.flags) | extra_flags)
        notes = ctx1.validation.notes
        if extra_flags and not stripped:
            notes = (notes + " " if notes else "") + "Transcript vacío; contexto por defecto."
        ctx2 = replace(ctx1, validation=GlobalContextValidation(flags=merged_flags, notes=notes.strip()))

        fp = hashlib.sha256(stripped.encode("utf-8", errors="ignore")).hexdigest()[:40]
        new_id = str(uuid.uuid4())
        ctx3 = replace(
            ctx2,
            id=new_id,
            project_id=project_correlation_id,
            transcript_fingerprint=fp,
        )

        vector: list[float] | None = None
        embed_id: str | None = None
        if generate_embedding and self._embedding is not None and stripped:
            t1 = time.perf_counter()
            embed_text = self._embedding_text(ctx3, stripped)
            try:
                vector, embed_id = self._embedding.embed_context(embed_text)
                logger.info(
                    "[GlobalContext] embedding_ok id=%s dim=%s elapsed_ms=%.1f",
                    embed_id,
                    len(vector) if vector else 0,
                    (time.perf_counter() - t1) * 1000,
                )
            except Exception as e:
                logger.warning("[GlobalContext] embedding_failed error=%s", e)
        ctx_final = replace(ctx3, embedding_vector_id=embed_id)
        logger.info(
            "[GlobalContext] complete id=%s industry=%s elapsed_ms=%.1f",
            ctx_final.id,
            ctx_final.industry.value,
            (time.perf_counter() - t0) * 1000,
        )
        return ctx_final, vector

    def _embedding_text(self, ctx: GlobalContext, stripped: str) -> str:
        anchors = " ".join(ctx.semantic_anchors)
        return (
            f"{ctx.topic}. {ctx.industry.value}. {ctx.product_context}. {ctx.cinematic_context}. "
            f"{anchors}. excerpt: {stripped[:1200]}"
        )
