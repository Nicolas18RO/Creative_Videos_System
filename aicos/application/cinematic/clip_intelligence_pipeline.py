"""Pipeline de enriquecimiento de clips (etapas instrumentadas; I/O vía puertos)."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from aicos.application.cinematic.emotion_analysis_service import EmotionAnalysisService
from aicos.application.cinematic.narrative_classifier_service import NarrativeClassifierService
from aicos.application.cinematic.ports import (
    ClipSemanticMetadataRepositoryPort,
    EmbeddingWriterPort,
    FrameExtractorPort,
    VisualAnalysisPort,
)
from aicos.application.cinematic.visual_intent_extraction_service import VisualIntentExtractionService
from aicos.domain.cinematic.entities import ClipSemanticMetadata
from aicos.domain.cinematic.enums import (
    CinematicStyle,
    EnergyLevel,
    MarketingUsage,
    NarrativeRole,
    Pacing,
)

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ClipIntelligencePipeline:
    """Orquesta extracción de frames, análisis textual y persistencia de metadata."""

    frame_extractor: FrameExtractorPort
    visual_analyzer: VisualAnalysisPort
    narrative_service: NarrativeClassifierService
    emotion_service: EmotionAnalysisService
    visual_intent_service: VisualIntentExtractionService
    metadata_repo: ClipSemanticMetadataRepositoryPort | None = None
    embedding_writer: EmbeddingWriterPort | None = None

    def run(
        self,
        clip_id: str,
        video_path: Path,
        transcript: str,
        *,
        scene_text: str = "",
        context: str | None = None,
        max_keyframes: int = 4,
    ) -> ClipSemanticMetadata:
        t_pipeline = time.perf_counter()
        # 1–2 frames
        t0 = time.perf_counter()
        frames = self.frame_extractor.extract_keyframe_paths(video_path, max_keyframes)
        logger.info(
            "metadata_generation stage=frame_extraction frames=%d elapsed_ms=%.1f",
            len(frames),
            (time.perf_counter() - t0) * 1000,
        )
        # 3 visual
        t0 = time.perf_counter()
        visual_desc = self.visual_analyzer.describe_frames(frames)
        logger.info(
            "metadata_generation stage=visual_analysis model=stub elapsed_ms=%.1f",
            (time.perf_counter() - t0) * 1000,
        )
        # 4–6 texto
        text_blob = scene_text or transcript
        narr, narr_prov = self.narrative_service.classify(transcript, text_blob, context)
        emotion = self.emotion_service.analyze(transcript, text_blob, pacing_hint=narr.pacing_recommendation)
        intents = self.visual_intent_service.extract(transcript, text_blob)
        intent_labels = tuple(v.intent_type.value for v in intents)
        # 7 embedding (opcional)
        embed_id: str | None = None
        if self.embedding_writer is not None:
            t0 = time.perf_counter()
            embed_id = self.embedding_writer.write_clip_embedding(
                clip_id, f"{visual_desc}\n{transcript}\n{text_blob}"
            )
            logger.info(
                "metadata_generation stage=embedding_generation ok=%s elapsed_ms=%.1f",
                embed_id is not None,
                (time.perf_counter() - t0) * 1000,
            )
        # Energía / pacing heurísticos desde emoción + narrativa
        energy = EnergyLevel.MEDIUM
        if emotion.emotional_intensity > 0.75:
            energy = EnergyLevel.HIGH
        elif emotion.emotional_intensity < 0.4:
            energy = EnergyLevel.LOW
        pacing = Pacing.MEDIUM
        if narr.pacing_recommendation.upper() == "FAST":
            pacing = Pacing.FAST
        elif narr.pacing_recommendation.upper() == "SLOW":
            pacing = Pacing.SLOW
        hook = 0.55 if narr.narrative_role == NarrativeRole.HOOK else 0.35
        cta = 0.6 if narr.narrative_role == NarrativeRole.CTA else 0.25
        now = datetime.now(timezone.utc)
        meta = ClipSemanticMetadata(
            clip_id=clip_id,
            visual_description=visual_desc[:4000],
            primary_emotion=emotion.primary_emotion,
            secondary_emotions=emotion.secondary_emotions,
            energy_level=energy,
            pacing=pacing,
            cinematic_style=CinematicStyle.TIKTOK_NATIVE,
            marketing_usage=MarketingUsage.CONVERSION
            if narr.narrative_role in (NarrativeRole.CTA, NarrativeRole.BENEFIT)
            else MarketingUsage.AWARENESS,
            narrative_roles=(narr.narrative_role,),
            visual_intents=intent_labels,
            hook_strength=hook,
            cta_strength=cta,
            emotional_intensity=emotion.emotional_intensity,
            semantic_tags=tuple({narr.narrative_role.value, emotion.primary_emotion.value}),
            searchable_keywords=tuple(
                sorted(set(narr.compatible_visual_styles) | set(intent_labels))[:32]
            ),
            embedding_vector_id=embed_id,
            created_at=now,
            updated_at=now,
        )
        if self.metadata_repo is not None:
            t0 = time.perf_counter()
            self.metadata_repo.upsert_clip_semantic_metadata(meta)
            logger.info(
                "metadata_generation stage=persistence elapsed_ms=%.1f",
                (time.perf_counter() - t0) * 1000,
            )
        logger.info(
            "metadata_generation stage=pipeline_complete clip_id=%s elapsed_ms=%.1f narrative_provider=%s",
            clip_id,
            (time.perf_counter() - t_pipeline) * 1000,
            narr_prov,
        )
        return meta
