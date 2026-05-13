"""Motor SQLite y sesiones SQLAlchemy."""

from __future__ import annotations

import logging
from collections.abc import Generator
from datetime import datetime
from pathlib import Path

from contextlib import contextmanager

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Text,
    create_engine,
    event,
    func,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from aicos.config import get_config

logger = logging.getLogger(__name__)

naming = {"ix": "ix_%(column_0_label)s", "uq": "uq_%(table_name)s_%(column_0_name)s"}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=naming)


class ClipRow(Base):
    __tablename__ = "clips"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    filename: Mapped[str] = mapped_column(Text, nullable=False)
    relative_path: Mapped[str] = mapped_column(Text, nullable=False)
    absolute_path: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    gender: Mapped[str | None] = mapped_column(String(8), nullable=True)
    narrative_function: Mapped[str | None] = mapped_column(String(32), nullable=True)
    subcategory: Mapped[str | None] = mapped_column(String(256), nullable=True)
    context: Mapped[str | None] = mapped_column(String(256), nullable=True)
    variant_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_ai_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    resolution_width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    resolution_height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # `file_hash` es metadata física (dedupe/analytics), NO identidad semántica.
    file_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    embedding_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    semantic_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[str | None] = mapped_column(Text, nullable=True)
    taxonomy_auto_classified: Mapped[bool] = mapped_column(Boolean, default=False)
    taxonomy_manually_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    naming_compliant: Mapped[bool] = mapped_column(Boolean, default=True)
    needs_reclassification: Mapped[bool] = mapped_column(Boolean, default=False)
    asset_kind: Mapped[str] = mapped_column(String(32), default="video")
    times_used: Mapped[int] = mapped_column(Integer, default=0)
    thumbnail_path: Mapped[str | None] = mapped_column(Text, nullable=True)


class ClipCinematicMetadataRow(Base):
    """Metadatos de producción explícitos por clip (Fase 5, 1:1 con ``clips``)."""

    __tablename__ = "clip_cinematic_metadata"

    clip_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("clips.id", ondelete="CASCADE"), primary_key=True
    )
    source_video_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    source_video_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    master_reel_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    shooting_session_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    camera_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    production_group: Mapped[str | None] = mapped_column(String(128), nullable=True)
    visual_collection: Mapped[str | None] = mapped_column(String(128), nullable=True)
    creation_date: Mapped[str | None] = mapped_column(String(32), nullable=True)
    location_tag: Mapped[str | None] = mapped_column(String(128), nullable=True)
    visual_cluster_id_explicit: Mapped[str | None] = mapped_column(String(128), nullable=True)
    visual_embedding_fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True)
    provenance: Mapped[str] = mapped_column(String(24), nullable=False, default="explicit")
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp())


class ClipVisualEmbeddingRow(Base):
    """Embedding visual OpenCLIP persistido por clip (Fase 5.1)."""

    __tablename__ = "clip_visual_embeddings"

    clip_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("clips.id", ondelete="CASCADE"), primary_key=True
    )
    embedding_json: Mapped[str] = mapped_column(Text, nullable=False)
    model_tag: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    dimension: Mapped[int] = mapped_column(Integer, nullable=False)
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp())


class EditorialMetadataRow(Base):
    """Capa editorial humana por clip (Fase 5.3)."""

    __tablename__ = "editorial_metadata"

    clip_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("clips.id", ondelete="CASCADE"), primary_key=True
    )
    editorial_tags: Mapped[str] = mapped_column(Text, nullable=False, default="")
    editorial_notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    visual_cluster_override: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    narrative_role: Mapped[str | None] = mapped_column(String(128), nullable=True)
    emotion_profile: Mapped[str | None] = mapped_column(String(128), nullable=True)
    visual_style: Mapped[str | None] = mapped_column(String(128), nullable=True)
    cinematic_style: Mapped[str | None] = mapped_column(String(128), nullable=True)
    pacing_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    shot_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    editorial_source_video_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    editorial_master_reel_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    cinematic_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    reviewed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    reviewed_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    correction_history_json: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp()
    )


class EditorialFeedbackRow(Base):
    """Feedback humano estructurado por clip (Fase 5.3)."""

    __tablename__ = "editorial_feedback"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    clip_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("clips.id", ondelete="CASCADE"), nullable=False, index=True
    )
    usefulness_score: Mapped[float] = mapped_column(Float, nullable=False)
    continuity_score: Mapped[float] = mapped_column(Float, nullable=False)
    diversity_score: Mapped[float] = mapped_column(Float, nullable=False)
    narrative_quality: Mapped[float] = mapped_column(Float, nullable=False)
    visual_quality: Mapped[float] = mapped_column(Float, nullable=False)
    human_feedback: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp())


class ProjectRow(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    product_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    product_category: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_audience: Mapped[str | None] = mapped_column(Text, nullable=True)
    audio_file_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    transcript_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="draft")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class GlobalContextRow(Base):
    """Contexto narrativo global por proyecto (Fase 1 Global Context Engine)."""

    __tablename__ = "global_contexts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    transcript_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    topic: Mapped[str] = mapped_column(Text, nullable=False)
    industry: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    dominant_emotion: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    narrative_arc: Mapped[str] = mapped_column(String(48), nullable=False, index=True)
    visual_style: Mapped[str] = mapped_column(String(48), nullable=False)
    content_intent: Mapped[str] = mapped_column(String(32), nullable=False)
    cinematic_context: Mapped[str] = mapped_column(Text, nullable=False)
    product_context: Mapped[str] = mapped_column(Text, nullable=False)
    continuity_context: Mapped[str] = mapped_column(Text, nullable=False)
    semantic_entities_json: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    semantic_anchors_json: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    secondary_industries_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    flags_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    validation_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    embedding_vector_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    provider: Mapped[str] = mapped_column(String(32), nullable=False, default="rules")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp())


class GlobalContextEntityRow(Base):
    """Entidades y anclas semánticas normalizadas."""

    __tablename__ = "global_context_entities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    global_context_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("global_contexts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    label: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    kind: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)


class GlobalContextEmbeddingRow(Base):
    """Vector de embedding global (referencia + payload JSON)."""

    __tablename__ = "global_context_embeddings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    global_context_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("global_contexts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(String(64), nullable=False, default="local")
    model_hint: Mapped[str | None] = mapped_column(String(256), nullable=True)
    dimensions: Mapped[int] = mapped_column(Integer, nullable=False)
    vector_json: Mapped[list] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp())


class SceneRow(Base):
    __tablename__ = "scenes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    global_context_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    scene_index: Mapped[int] = mapped_column(Integer, nullable=False)
    start_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    end_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    concept: Mapped[str] = mapped_column(Text, nullable=False, default="")
    narrative_function: Mapped[str] = mapped_column(String(32), nullable=False)
    is_hook: Mapped[bool] = mapped_column(Boolean, default=False)
    hook_score: Mapped[float] = mapped_column(Float, default=0.0)
    gender_hint: Mapped[str | None] = mapped_column(String(8), nullable=True)
    selected_clip_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    gap_detected: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp())


class RecommendationRow(Base):
    __tablename__ = "recommendations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    scene_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("scenes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    clip_id: Mapped[str] = mapped_column(String(64), nullable=False)
    similarity_score: Mapped[float] = mapped_column(Float, nullable=False)
    taxonomy_boost: Mapped[float] = mapped_column(Float, default=0.0)
    final_score: Mapped[float] = mapped_column(Float, nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    accepted: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    shown_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp())


class UsageEventRow(Base):
    """Memoria de uso para inteligencia de recuperación (Fase 3 PRD, sin ML)."""

    __tablename__ = "usage_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp())
    event_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    clip_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    query_fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    narrative_function: Mapped[str | None] = mapped_column(String(32), nullable=True)
    scene_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    project_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    payload: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)


class GapRow(Base):
    __tablename__ = "gaps"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    scene_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("scenes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    concept: Mapped[str] = mapped_column(Text, nullable=False)
    narrative_function: Mapped[str] = mapped_column(String(32), nullable=False)
    gap_type: Mapped[str] = mapped_column(String(32), nullable=False)
    tiktok_keywords: Mapped[list | None] = mapped_column(JSON, nullable=True)
    ai_image_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_motion_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    taxonomy_suggestion: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolution_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    resolved_clip_id: Mapped[str | None] = mapped_column(String(36), nullable=True)


class ClipSemanticMetadataRow(Base):
    """Metadata semántica enriquecida por clip (payload JSON + columnas indexables)."""

    __tablename__ = "clip_semantic_metadata"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    clip_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("clips.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    embedding_vector_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    primary_emotion: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    energy_level: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    pacing: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    dominant_narrative_role: Mapped[str | None] = mapped_column(String(48), nullable=True, index=True)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp()
    )


class SceneSemanticAnalysisRow(Base):
    """Resumen semántico por escena (JSON extensible)."""

    __tablename__ = "scene_semantic_analysis"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    scene_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("scenes.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp()
    )


class EmotionAnalysisRow(Base):
    """Análisis emocional (escena o clip vía FK opcional)."""

    __tablename__ = "emotion_analysis"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    scene_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("scenes.id", ondelete="CASCADE"), nullable=True, index=True
    )
    clip_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("clips.id", ondelete="CASCADE"), nullable=True, index=True
    )
    primary_emotion: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    emotional_intensity: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp())


class VisualIntentRow(Base):
    """Intenciones visuales inferidas (una fila por escena con lista serializada)."""

    __tablename__ = "visual_intents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    scene_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("scenes.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    intents_json: Mapped[list] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp())


class NarrativeAnalysisRow(Base):
    """Clasificación narrativa por escena."""

    __tablename__ = "narrative_analysis"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    scene_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("scenes.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    narrative_role: Mapped[str] = mapped_column(String(48), nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    reasoning: Mapped[str] = mapped_column(Text, nullable=False, default="")
    compatible_visual_styles: Mapped[list | None] = mapped_column(JSON, nullable=True)
    pacing_recommendation: Mapped[str | None] = mapped_column(String(64), nullable=True)
    provider: Mapped[str] = mapped_column(String(32), nullable=False, default="rules")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp())


class FeedbackEventRow(Base):
    """Eventos de feedback para aprendizaje de ranking (aceptar, rechazar, reordenar)."""

    __tablename__ = "feedback_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp(), index=True)
    event_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    clip_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    scene_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    project_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    acceptance_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class RankingHistoryRow(Base):
    """Traza de factores de ranking para auditoría y reranking."""

    __tablename__ = "ranking_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp(), index=True)
    query_fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    clip_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    scene_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    final_score: Mapped[float] = mapped_column(Float, nullable=False)
    factors_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class NarrativeSessionRow(Base):
    """Sesión de memoria narrativa (p. ej. un análisis de audio por correlation_id)."""

    __tablename__ = "narrative_sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp()
    )


class NarrativeMemorySnapshotRow(Base):
    """Instantánea del estado de memoria tras cada escena."""

    __tablename__ = "narrative_memory_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    narrative_session_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("narrative_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    scene_index: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    state_payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp())


class NarrativeClipSelectionHistoryRow(Base):
    """Historial del clip priorizado (típicamente rank 1) por escena."""

    __tablename__ = "narrative_clip_selection_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    narrative_session_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("narrative_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    scene_index: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    clip_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    rank_chosen: Mapped[int] = mapped_column(Integer, nullable=False)
    final_score: Mapped[float] = mapped_column(Float, nullable=False)
    continuity_blend: Mapped[float | None] = mapped_column(Float, nullable=True)
    extra_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp())


class NarrativeContinuityDecisionRow(Base):
    """Decisiones de continuidad o bloqueo temático (auditoría)."""

    __tablename__ = "narrative_continuity_decisions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    narrative_session_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("narrative_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    scene_index: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    clip_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    decision_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    reason_code: Mapped[str] = mapped_column(String(96), nullable=False)
    factors_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp())


class ClipUsageHistoryRow(Base):
    """Historial opcional de selección con señales de diversidad (Fase 4, analytics)."""

    __tablename__ = "clip_usage_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    correlation_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    scene_index: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    clip_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_video_id: Mapped[str] = mapped_column(String(32), nullable=False, default="", index=True)
    visual_cluster_id: Mapped[str] = mapped_column(String(32), nullable=False, default="", index=True)
    final_score: Mapped[float] = mapped_column(Float, nullable=False)
    penalties_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp())


_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        paths = get_config().resolved_paths()
        db_path: Path = paths["database"]
        db_path.parent.mkdir(parents=True, exist_ok=True)
        _engine = create_engine(
            f"sqlite:///{db_path}",
            echo=False,
            future=True,
            connect_args={"check_same_thread": False, "timeout": 30},
        )

        @event.listens_for(_engine, "connect")
        def _sqlite_pragma(dbapi_connection, _connection_record) -> None:
            cur = dbapi_connection.cursor()
            cur.execute("PRAGMA foreign_keys=ON")
            cur.close()

    return _engine


def get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(get_engine(), expire_on_commit=False, class_=Session)
    return _SessionLocal


def init_db() -> None:
    """Crea tablas si no existen."""
    eng = get_engine()
    Base.metadata.create_all(eng)
    _migrate_drop_unique_file_hash(eng)
    _migrate_scenes_add_global_context_id(eng)
    logger.info("SQLite inicializado en %s", eng.url)


def _migrate_scenes_add_global_context_id(engine) -> None:
    """Añade ``global_context_id`` a ``scenes`` en bases existentes."""
    with engine.begin() as conn:
        exists = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='scenes'")
        ).scalar_one_or_none()
        if not exists:
            return
        rows = conn.execute(text("PRAGMA table_info(scenes)")).fetchall()
        names = {r[1] for r in rows}
        if "global_context_id" in names:
            return
        conn.execute(text("ALTER TABLE scenes ADD COLUMN global_context_id VARCHAR(36)"))
        conn.execute(
            text("CREATE INDEX IF NOT EXISTS ix_scenes_global_context_id ON scenes(global_context_id)")
        )
        logger.info("Migrando SQLite: añadida columna scenes.global_context_id")


def _migrate_drop_unique_file_hash(engine) -> None:
    """Elimina UNIQUE(file_hash) de `clips` si existe (migración SQLite segura).

    SQLite no soporta DROP CONSTRAINT; se recrea la tabla y se copian datos.
    """
    with engine.begin() as conn:
        # Si la tabla no existe (primera corrida), no hay nada que migrar.
        exists = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='clips'")
        ).scalar_one_or_none()
        if not exists:
            return

        indexes = conn.execute(text("PRAGMA index_list('clips')")).fetchall()
        unique_index_on_file_hash = False
        for idx in indexes:
            # PRAGMA index_list: (seq, name, unique, origin, partial)
            name = idx[1]
            unique = int(idx[2]) == 1
            if not unique:
                continue
            cols = conn.execute(text(f"PRAGMA index_info('{name}')")).fetchall()
            col_names = [c[2] for c in cols]  # (seqno, cid, name)
            if col_names == ["file_hash"]:
                unique_index_on_file_hash = True
                break

        if not unique_index_on_file_hash:
            return

        logger.warning("Migrando SQLite: removiendo UNIQUE(file_hash) de clips...")

        # Rebuild table without UNIQUE(file_hash). Keep UNIQUE(absolute_path).
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS clips_new (
                    id VARCHAR(36) PRIMARY KEY,
                    filename TEXT NOT NULL,
                    relative_path TEXT NOT NULL,
                    absolute_path TEXT NOT NULL UNIQUE,
                    gender VARCHAR(8),
                    narrative_function VARCHAR(32),
                    subcategory VARCHAR(256),
                    context VARCHAR(256),
                    variant_number INTEGER,
                    is_ai_generated BOOLEAN,
                    duration_ms INTEGER,
                    resolution_width INTEGER,
                    resolution_height INTEGER,
                    file_size_bytes INTEGER,
                    file_hash VARCHAR(64),
                    embedding_id VARCHAR(64),
                    semantic_text TEXT,
                    tags TEXT,
                    taxonomy_auto_classified BOOLEAN,
                    taxonomy_manually_verified BOOLEAN,
                    naming_compliant BOOLEAN,
                    needs_reclassification BOOLEAN,
                    asset_kind VARCHAR(32),
                    times_used INTEGER,
                    thumbnail_path TEXT
                )
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO clips_new (
                    id, filename, relative_path, absolute_path, gender, narrative_function, subcategory, context,
                    variant_number, is_ai_generated, duration_ms, resolution_width, resolution_height, file_size_bytes,
                    file_hash, embedding_id, semantic_text, tags, taxonomy_auto_classified, taxonomy_manually_verified,
                    naming_compliant, needs_reclassification, asset_kind, times_used, thumbnail_path
                )
                SELECT
                    id, filename, relative_path, absolute_path, gender, narrative_function, subcategory, context,
                    variant_number, is_ai_generated, duration_ms, resolution_width, resolution_height, file_size_bytes,
                    file_hash, embedding_id, semantic_text, tags, taxonomy_auto_classified, taxonomy_manually_verified,
                    naming_compliant, needs_reclassification, asset_kind, times_used, thumbnail_path
                FROM clips
                """
            )
        )
        conn.execute(text("DROP TABLE clips"))
        conn.execute(text("ALTER TABLE clips_new RENAME TO clips"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_clips_file_hash ON clips(file_hash)"))

@contextmanager
def session_scope() -> Generator[Session, None, None]:
    SessionLocal = get_session_factory()
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def __getattr__(name: str):
    """Expone ``engine`` como alias perezoso de ``get_engine()`` (singleton único, sin duplicar creación)."""
    if name == "engine":
        return get_engine()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
