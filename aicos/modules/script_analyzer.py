"""Orquestación M1 + M2 + M3 sobre un archivo de audio."""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from pathlib import Path

from aicos.core import concept_extractor, segmenter, transcriber
from aicos.core.embedder import Embedder
from aicos.core.vector_store import VectorStore
from aicos.database.db import session_scope
from aicos.models.schemas import (
    AnalyzedScene,
    AnalyzeAPIResponse,
    Scene,
    SearchRequest,
    SearchResponse,
    Transcript,
)
from aicos.modules import clip_recommender, gap_handler
from aicos.services import audio_intelligence_service
from aicos.services.analyze_exceptions import wrap_stage_exception

logger = logging.getLogger(__name__)


def _log_stage(stage: str, t0: float) -> None:
    elapsed = time.perf_counter() - t0
    logger.info("[Analyze] Stage=%s elapsed=%.3fs", stage, elapsed)


async def analyze_audio(
    audio_path: str | Path,
    *,
    project_name: str = "Proyecto",
    product_category: str = "salud/bienestar",
    target_audience: str = "adultos 35-55",
    gender_hint_default: str | None = None,
    include_clip_search: bool = True,
    enable_intelligence: bool = True,
) -> AnalyzeAPIResponse:
    """Pipeline: transcribir → segmentar → conceptos → búsqueda → gaps.

    Con ``enable_intelligence`` las búsquedas pasan por ``search_service`` (memoria de uso).
    """
    t_pipeline = time.perf_counter()
    path = Path(audio_path).resolve()
    warning: str | None = None
    analysis_project_id = str(uuid.uuid4())

    logger.info(
        "[Analyze] START project_id=%s path=%s include_clip_search=%s enable_intelligence=%s",
        analysis_project_id,
        path,
        include_clip_search,
        enable_intelligence,
    )

    try:
        t0 = time.perf_counter()
        transcript = await asyncio.to_thread(transcriber.transcribe, path)
        _log_stage("transcription", t0)
    except Exception as e:
        logger.exception("[Analyze] Stage=transcription FAILED")
        raise wrap_stage_exception("transcription", e) from e

    global_ctx_id: str | None = None
    global_summary = None
    gc_vector: list[float] | None = None
    enrichment_line: str | None = None
    try:
        t0 = time.perf_counter()
        from aicos.application.context.query_enrichment import build_global_query_enrichment
        from aicos.services.context_repository import domain_global_context_to_summary
        from aicos.services.global_context_factory import build_global_context_service

        gcs = build_global_context_service(with_embedding=include_clip_search)
        gctx, gc_vector = gcs.build_from_transcript(
            transcript.full_text,
            project_correlation_id=analysis_project_id,
            product_category=product_category,
            target_audience=target_audience,
            generate_embedding=include_clip_search,
        )
        global_summary = domain_global_context_to_summary(gctx)
        global_ctx_id = gctx.id
        enrichment_line = build_global_query_enrichment(gctx)
        _log_stage("global_context_engine", t0)
    except Exception as e:
        logger.exception("[Analyze] Stage=global_context_engine FAILED")
        wrapped = wrap_stage_exception("global_context_engine", e)
        warning = (warning + " " if warning else "") + f"Global context degradado: {wrapped.message}"
        global_ctx_id = None
        global_summary = None
        gc_vector = None
        enrichment_line = None

    try:
        t0 = time.perf_counter()
        scenes = segmenter.segment(transcript)
        _log_stage("segmentation", t0)
    except Exception as e:
        logger.exception("[Analyze] Stage=segmentation FAILED")
        raise wrap_stage_exception("segmentation", e) from e

    if not scenes:
        warn_extra = (
            "Transcripción vacía o sin palabras segmentables; "
            "revisa audio válido, idioma en config o calidad de micrófono."
        )
        warning = (warning + " " if warning else "") + warn_extra
        logger.warning("[Analyze] Stage=segmentation empty_scenes=true duration_ms=%s", transcript.duration_ms)

    total_ms = transcript.duration_ms
    hook_count = sum(1 for s in scenes if s.is_hook)

    llm = None

    enriched: list[Scene] = []
    try:
        t0 = time.perf_counter()
        for s in scenes:
            gh = s.gender_hint or gender_hint_default
            concept = await concept_extractor.extract_concept(
                s.text,
                s.narrative_function,
                llm,
                global_query_enrichment=enrichment_line,
            )
            enriched.append(
                s.model_copy(
                    update={
                        "concept": concept,
                        "gender_hint": gh,
                        "project_id": analysis_project_id,
                        "global_context_id": global_ctx_id,
                        "global_query_enrichment": enrichment_line,
                    }
                )
            )
        _log_stage("concept_extraction", t0)
    except Exception as e:
        logger.exception("[Analyze] Stage=concept_extraction FAILED")
        raise wrap_stage_exception("concept_extraction", e) from e

    embedder: Embedder | None = None
    store: VectorStore | None = None
    if include_clip_search:
        try:
            t0 = time.perf_counter()
            embedder = Embedder()
            store = VectorStore()
            _log_stage("embeddings_and_vector_store_init", t0)
        except Exception as e:
            logger.exception("[Analyze] Stage=embeddings_and_vector_store_init FAILED")
            wrapped = wrap_stage_exception("embeddings_and_vector_store_init", e)
            warning = (warning + " " if warning else "") + f"Búsqueda de clips desactivada: {wrapped.message}"
            include_clip_search = False

    analyzed: list[AnalyzedScene] = []
    used_clip_ids: list[str] = []
    clip_usage_records: list = []

    if include_clip_search and embedder and store and enable_intelligence:
        try:
            t0 = time.perf_counter()
            with session_scope() as session:
                for idx, s in enumerate(enriched):
                    recs: list = []
                    gap = None
                    prior_concepts = [enriched[i].concept for i in range(idx)] if idx else []
                    resp = audio_intelligence_service.run_analyze_scene_search(
                        session,
                        scene=s,
                        embedder=embedder,
                        store=store,
                        used_clip_ids=used_clip_ids,
                        correlation_id=analysis_project_id,
                        scene_index=idx,
                        enable_intelligence=True,
                        global_query_enrichment=enrichment_line,
                        global_context=global_summary,
                        prior_scene_concepts=prior_concepts,
                        clip_usage_records=clip_usage_records,
                    )
                    recs = resp.results
                    is_gap = resp.is_gap
                    if recs:
                        used_clip_ids.append(recs[0].clip_id)
                    if is_gap:
                        try:
                            gap = await gap_handler.enrich_gap(
                                s,
                                resp,
                                None,
                                product_category=product_category,
                                target_audience=target_audience,
                            )
                        except Exception as e:
                            logger.warning("[Analyze] gap_handler scene_index=%s: %s", idx, e)
                    analyzed.append(AnalyzedScene(scene=s, recommendations=recs, is_gap=is_gap, gap=gap))
            _log_stage("semantic_search_intelligence", t0)
        except Exception as e:
            logger.exception("[Analyze] Stage=semantic_search_intelligence FAILED")
            raise wrap_stage_exception("semantic_search", e) from e
    else:
        try:
            t0 = time.perf_counter()
            for s in enriched:
                recs = []
                gap = None
                if include_clip_search and embedder and store:
                    req = SearchRequest(
                        query=s.concept,
                        narrative_function=s.narrative_function,
                        gender_hint=s.gender_hint,
                        is_hook=s.is_hook,
                        used_clip_ids=list(used_clip_ids),
                        global_query_enrichment=enrichment_line,
                    )
                    resp = await asyncio.to_thread(clip_recommender.recommend, req, embedder, store)
                    recs = resp.results
                    is_gap = resp.is_gap
                    if recs:
                        used_clip_ids.append(recs[0].clip_id)
                else:
                    resp = SearchResponse(results=[], is_gap=True)
                    is_gap = True

                if is_gap:
                    try:
                        gap = await gap_handler.enrich_gap(
                            s,
                            resp,
                            None,
                            product_category=product_category,
                            target_audience=target_audience,
                        )
                    except Exception as e:
                        logger.warning("[Analyze] gap_handler escena: %s", e)

                analyzed.append(AnalyzedScene(scene=s, recommendations=recs, is_gap=is_gap, gap=gap))
            _log_stage("semantic_search_legacy", t0)
        except Exception as e:
            logger.exception("[Analyze] Stage=semantic_search_legacy FAILED")
            raise wrap_stage_exception("semantic_search", e) from e

    logger.info(
        "[Analyze] DONE project_id=%s scenes=%s total_pipeline_elapsed=%.3fs",
        analysis_project_id,
        len(analyzed),
        time.perf_counter() - t_pipeline,
    )

    return AnalyzeAPIResponse(
        project_id=analysis_project_id,
        project_name=project_name,
        transcript=transcript,
        total_duration_ms=total_ms,
        hook_count=hook_count,
        scenes=analyzed,
        warning=warning,
        global_context_id=global_ctx_id,
        global_context=global_summary,
        global_context_embedding_vector=gc_vector,
    )
