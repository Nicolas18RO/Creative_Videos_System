"""Factoría de composición para servicios de inteligencia cinematográfica."""

from __future__ import annotations

from aicos.application.cinematic.clip_intelligence_pipeline import ClipIntelligencePipeline
from aicos.application.cinematic.emotion_analysis_service import EmotionAnalysisService
from aicos.application.cinematic.narrative_classifier_service import NarrativeClassifierService
from aicos.application.cinematic.providers.future_openai_narrative import FutureOpenAINarrativeProvider
from aicos.application.cinematic.providers.local_llm_narrative import LocalLLMNarrativeProvider
from aicos.application.cinematic.rule_based_narrative import RuleBasedNarrativeProvider
from aicos.application.cinematic.smart_clip_ranking import SmartClipRankingService
from aicos.application.cinematic.visual_intent_extraction_service import VisualIntentExtractionService
from aicos.config import AppConfig, get_config
from aicos.services.cinematic_frame_extractor import FfmpegKeyframeExtractor
from aicos.services.cinematic_intel_repository import SqlCinematicIntelRepository
from aicos.services.cinematic_visual_stub import StubVisualAnalysisAdapter
from aicos.services.ffmpeg_service import FFmpegService


def build_sql_cinematic_repository() -> SqlCinematicIntelRepository:
    return SqlCinematicIntelRepository()


def build_narrative_classifier_service(cfg: AppConfig | None = None) -> NarrativeClassifierService:
    c = cfg or get_config()
    providers = [
        LocalLLMNarrativeProvider(enabled=False),
        RuleBasedNarrativeProvider(),
        FutureOpenAINarrativeProvider(),
    ]
    return NarrativeClassifierService(
        providers=providers,
        provider_order=tuple(c.cinematic_intel.narrative_provider_order),
    )


def build_emotion_analysis_service(cfg: AppConfig | None = None) -> EmotionAnalysisService:
    c = cfg or get_config()
    return EmotionAnalysisService(deterministic=c.cinematic_intel.emotion_deterministic)


def build_visual_intent_extraction_service() -> VisualIntentExtractionService:
    return VisualIntentExtractionService()


def build_smart_clip_ranking_service(cfg: AppConfig | None = None) -> SmartClipRankingService:
    c = cfg or get_config()
    return SmartClipRankingService(config=c.cinematic_intel)


def build_clip_intelligence_pipeline(
    cfg: AppConfig | None = None,
    *,
    metadata_repo: SqlCinematicIntelRepository | None = None,
) -> ClipIntelligencePipeline:
    """Ensambla pipeline con FFmpeg (keyframes) y stubs de visión/embeddings."""
    c = cfg or get_config()
    paths = c.resolved_paths()
    ffmpeg = FFmpegService()
    extractor = FfmpegKeyframeExtractor(
        ffmpeg=ffmpeg,
        cache_root=paths["thumbnails_cache"],
        width=c.cinematic_intel.pipeline_keyframe_width,
        height=c.cinematic_intel.pipeline_keyframe_height,
    )
    repo = metadata_repo if metadata_repo is not None else SqlCinematicIntelRepository()
    return ClipIntelligencePipeline(
        frame_extractor=extractor,
        visual_analyzer=StubVisualAnalysisAdapter(),
        narrative_service=build_narrative_classifier_service(c),
        emotion_service=build_emotion_analysis_service(c),
        visual_intent_service=build_visual_intent_extraction_service(),
        metadata_repo=repo,
        embedding_writer=None,
    )
