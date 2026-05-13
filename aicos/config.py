"""Carga y resolución de rutas de `config.yaml`."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import AliasChoices, BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


def _expand(p: str) -> Path:
    return Path(os.path.expandvars(os.path.expanduser(p))).resolve()


class RuntimeConfig(BaseModel):
    """Modo de ejecución: local-first sin llamadas a nube por defecto."""

    use_openai: bool = False
    offline_mode: bool = True
    local_only: bool = True


class PathsConfig(BaseModel):
    library_root: str = "."
    incoming_folder: str = "./incoming"
    thumbnails_cache: str = "~/.aicos/thumbnails"
    database: str = "~/.aicos/aicos.db"
    vector_store: str = "~/.aicos/vector_store"
    logs: str = "~/.aicos/logs"
    exports: str = "~/.aicos/exports"


class TranscriptionConfig(BaseModel):
    engine: str = "faster_whisper"
    model: str = "small"
    language: str | None = "es"
    word_timestamps: bool = True
    device: str = "cpu"


class EmbeddingsConfig(BaseModel):
    """Embeddings semánticos: `local` (sentence-transformers) u `openai`."""

    provider: str = "local"
    model: str = "sentence-transformers/all-MiniLM-L6-v2"
    dimensions: int = 1536
    device: str = "auto"
    batch_size: int = 64
    normalize_embeddings: bool = True
    collection_name: str | None = None


class LLMConfig(BaseModel):
    provider: str = "local"
    model: str = "gpt-4o"
    temperature: float = 0.3
    max_tokens: int = 1000


class VisionConfig(BaseModel):
    provider: str = "local"
    model: str = "gpt-4o"
    classification_confidence_threshold: float = 0.75


class SearchConfig(BaseModel):
    default_n_results: int = 5
    candidate_pool_size: int = 15
    gap_threshold: float = 0.65
    narrative_function_boost: float = 0.20
    gender_match_boost: float = 0.10
    hook_category_boost: float = 0.25
    repeat_clip_penalty: float = 0.15


class IntelligenceConfig(BaseModel):
    """Memoria de uso y boosts de ranking (Fase 3 PRD, sin re-embeddings)."""

    half_life_days: float = 30.0
    max_intelligence_boost: float = 0.12
    min_intelligence_boost: float = -0.08
    search_exposure_weight: float = 0.012
    feedback_positive_weight: float = 0.055
    feedback_negative_weight: float = -0.045
    event_lookback_days: int = 120
    audio_segment_signal_weight: float = 0.011
    audio_repeat_clip_penalty: float = 0.022


class SegmentationConfig(BaseModel):
    target_duration_ms: int = 2500
    max_duration_ms: int = 4000
    min_duration_ms: int = 800
    hook_window_ms: int = 7000
    silence_threshold_ms: int = 400


class OrganizerConfig(BaseModel):
    auto_classify: bool = False
    watch_interval_seconds: int = 1
    batch_processing: bool = True


class IncomingWatcherConfig(BaseModel):
    """Observador de carpeta `incoming/` (M4 en segundo plano)."""

    enabled: bool = False
    # Tras crear un archivo, esperar antes de procesar (copias incompletas).
    settle_seconds: float = 2.0
    # Si no se mueve el clip, escribe `{archivo}.aicos.json` junto al video.
    write_sidecar: bool = True


class LibraryConfig(BaseModel):
    legacy_gender_prefixes: dict[str, str] = Field(
        default_factory=lambda: {"NEUTRAL": "N", "KID": "KIDS"}
    )
    ignore_patterns: list[str] = Field(
        default_factory=lambda: ["*.log", "mssdk*", "*.txt", ".DS_Store", "Thumbs.db"]
    )
    ignore_folders: list[str] = Field(default_factory=lambda: ["mssdk", ".aicos"])


class UIConfig(BaseModel):
    thumbnails_per_scene: int = 5
    thumbnail_size: tuple[int, int] = (160, 90)
    theme: str = "dark"


class CinematicIntelConfig(BaseModel):
    """Pesos y flags para ranking multi-factor y pipeline de inteligencia cinematográfica (local-first)."""

    narrative_provider_order: list[str] = Field(
        default_factory=lambda: ["local_llm", "rules", "future_openai"]
    )
    emotion_deterministic: bool = True
    # Pesos para SmartClipRankingService (suma ~1.0 recomendada; se renormaliza si hace falta).
    weight_semantic_similarity: float = 0.28
    weight_emotional_compatibility: float = 0.14
    weight_narrative_compatibility: float = 0.14
    weight_pacing_compatibility: float = 0.10
    weight_cinematic_compatibility: float = 0.10
    weight_visual_intent_compatibility: float = 0.12
    weight_feedback_score: float = 0.08
    weight_historical_performance: float = 0.04
    pipeline_max_keyframes: int = 4
    pipeline_keyframe_width: int = 320
    pipeline_keyframe_height: int = 180


class ContextualRetrievalConfig(BaseModel):
    """Fase 2: retrieval contextual post-Chroma (pesos sumables a 1.0)."""

    enabled: bool = True
    top_k_rerank: int = 40
    lazy_rerank: bool = True
    use_batch_context_embedding: bool = False
    embedding_batch_size: int = 16
    embedding_blend: float = 0.0
    diversity_balance_enabled: bool = True
    diversity_subcategory_penalty: float = 0.04
    weight_semantic: float = 0.35
    weight_global_context: float = 0.25
    weight_narrative: float = 0.15
    weight_domain: float = 0.10
    weight_emotion: float = 0.05
    weight_continuity: float = 0.05
    weight_cinematic_style: float = 0.05


class NarrativeMemoryConfig(BaseModel):
    """Fase 3: memoria narrativa persistente y continuidad de sesión (offline)."""

    enabled: bool = True
    window_size: int = 5
    continuity_weight: float = 0.25
    diversity_weight: float = 0.10
    industry_lock_strength: float = 0.70
    max_repeat_clip_penalty: float = 0.35
    subcategory_loop_penalty: float = 0.12


class ClipUsageIntelligenceConfig(BaseModel):
    """Fase 4: anti-repetición, diversidad de origen/cluster y alternancia de planes."""

    enabled: bool = True
    persist_history: bool = True
    exact_clip_penalty: float = 0.95
    same_source_penalty: float = 0.45
    same_cluster_penalty: float = 0.65
    diversity_weight: float = 0.30
    continuity_weight: float = 0.40
    hard_exclude_exact_reuse: bool = True
    min_alternatives_for_hard_exclude: int = 3
    allow_same_clip: bool = False
    allow_same_source_video: bool = True
    allow_same_visual_cluster: bool = True
    max_reuse_penalty_cap: float = 1.0
    narrative_overlap_penalty_scale: float = 0.35
    temporal_repeat_penalty: float = 0.22


class CinematicMetadataConfig(BaseModel):
    """Fase 5: metadatos de producción explícitos y embeddings visuales opcionales."""

    enabled: bool = True
    openclip_enabled: bool = False
    openclip_model: str = "ViT-B-32"
    openclip_pretrained: str = "laion2b_s34b_b79k"
    index_visual_fingerprint_in_chroma: bool = True


class MultimodalBatchConfig(BaseModel):
    """Fase 5.1: batch OpenCLIP sobre biblioteca (GPU-aware, escalable por lotes)."""

    enabled: bool = True
    batch_size: int = 8
    keyframe_width: int = 224
    keyframe_height: int = 224
    update_chroma: bool = True
    skip_existing_same_model: bool = True
    max_clips: int | None = Field(
        default=None,
        description="Si no es None, limita el número total de clips procesados (dry/lab).",
    )


class MultimodalRetrievalConfig(BaseModel):
    """Fase 5.2: regeneración Chroma multimodal + pesos de ranking híbrido."""

    enabled: bool = True
    batch_size: int = 128
    update_existing: bool = True
    skip_missing_fingerprints: bool = True
    persist_stats: bool = True
    enable_visual_similarity: bool = True
    visual_similarity_weight: float = 0.35
    regenerate_metadata: bool = True
    max_failures: int = 50
    strict_model_match: bool = False
    allow_visual_embedding_overwrite: bool = Field(
        default=False,
        description="Si true y la dimensión coincide con el embedding Chroma, sustituye el vector.",
    )


class EditorialMetadataConfig(BaseModel):
    """Fase 5.3: API editorial y boosts opcionales en retrieval."""

    enabled: bool = True
    allow_editorial_overrides: bool = True
    enable_editorial_boosts: bool = True
    editorial_quality_weight: float = 0.20
    cinematic_score_weight: float = 0.30
    persist_feedback: bool = True
    enable_bulk_operations: bool = True


class AppConfig(BaseModel):
    version: str = "2.0"
    runtime: RuntimeConfig = Field(default_factory=RuntimeConfig)
    paths: PathsConfig = Field(default_factory=PathsConfig)
    transcription: TranscriptionConfig = Field(default_factory=TranscriptionConfig)
    embeddings: EmbeddingsConfig = Field(default_factory=EmbeddingsConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    vision: VisionConfig = Field(default_factory=VisionConfig)
    search: SearchConfig = Field(default_factory=SearchConfig)
    intelligence: IntelligenceConfig = Field(default_factory=IntelligenceConfig)
    segmentation: SegmentationConfig = Field(default_factory=SegmentationConfig)
    organizer: OrganizerConfig = Field(default_factory=OrganizerConfig)
    incoming_watcher: IncomingWatcherConfig = Field(default_factory=IncomingWatcherConfig)
    library: LibraryConfig = Field(default_factory=LibraryConfig)
    ui: UIConfig = Field(default_factory=UIConfig)
    cinematic_intel: CinematicIntelConfig = Field(default_factory=CinematicIntelConfig)
    contextual_retrieval: ContextualRetrievalConfig = Field(default_factory=ContextualRetrievalConfig)
    narrative_memory: NarrativeMemoryConfig = Field(default_factory=NarrativeMemoryConfig)
    clip_usage_intelligence: ClipUsageIntelligenceConfig = Field(default_factory=ClipUsageIntelligenceConfig)
    cinematic_metadata: CinematicMetadataConfig = Field(default_factory=CinematicMetadataConfig)
    multimodal_batch: MultimodalBatchConfig = Field(default_factory=MultimodalBatchConfig)
    multimodal_retrieval: MultimodalRetrievalConfig = Field(default_factory=MultimodalRetrievalConfig)
    editorial_metadata: EditorialMetadataConfig = Field(default_factory=EditorialMetadataConfig)

    def resolved_paths(self) -> dict[str, Path]:
        return {
            "library_root": _expand(self.paths.library_root),
            "incoming_folder": _expand(self.paths.incoming_folder),
            "thumbnails_cache": _expand(self.paths.thumbnails_cache),
            "database": _expand(self.paths.database),
            "vector_store": _expand(self.paths.vector_store),
            "logs": _expand(self.paths.logs),
            "exports": _expand(self.paths.exports),
        }


class Settings(BaseSettings):
    """Variables de entorno (API keys, etc.)."""

    model_config = SettingsConfigDict(env_prefix="AICOS_", extra="ignore")

    openai_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("AICOS_OPENAI_API_KEY", "OPENAI_API_KEY"),
    )


def load_yaml_config(path: Path | None = None) -> AppConfig:
    """Carga `config.yaml` desde la raíz del proyecto o la ruta indicada."""
    cfg_path = path or Path(__file__).resolve().parent.parent / "config.yaml"
    if not cfg_path.is_file():
        logger.warning("No se encontró %s; usando valores por defecto", cfg_path)
        return AppConfig()
    data: dict[str, Any] = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    ui = data.get("ui") or {}
    if "thumbnail_size" in ui and isinstance(ui["thumbnail_size"], list):
        ui["thumbnail_size"] = tuple(ui["thumbnail_size"])
    data["ui"] = ui
    return AppConfig.model_validate(data)


_settings: AppConfig | None = None


def get_config(reload: bool = False) -> AppConfig:
    global _settings
    if _settings is None or reload:
        _settings = load_yaml_config()
    return _settings
