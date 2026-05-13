"""Puertos (protocolos) para inversión de dependencias — sin SQLAlchemy ni FastAPI."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from aicos.domain.cinematic.entities import (
    ClipSemanticMetadata,
    EmotionAnalysis,
    FeedbackEvent,
    NarrativeClassificationResult,
    VisualIntent,
)


class NarrativeClassifierProvider(Protocol):
    """Proveedor de clasificación narrativa (reglas, LLM local, futuro OpenAI)."""

    @property
    def provider_id(self) -> str:
        """Identificador estable (p. ej. ``rules``, ``local_llm``)."""

    def classify(
        self,
        transcript: str,
        scene_text: str,
        context: str | None = None,
    ) -> NarrativeClassificationResult | None:
        """Retorna ``None`` si este proveedor no aplica o no está disponible."""


class FrameExtractorPort(Protocol):
    """Extracción de fotogramas clave (implementación vía ``ffmpeg_service``)."""

    def extract_keyframe_paths(self, video_path: Path, max_frames: int) -> list[Path]:
        """Rutas a JPEG generados."""


class VisualAnalysisPort(Protocol):
    """Análisis visual local (OpenCLIP / visión futura); stub permitido."""

    def describe_frames(self, frame_paths: list[Path]) -> str:
        """Descripción agregada en lenguaje natural (puede ser heurística)."""


class EmbeddingWriterPort(Protocol):
    """Persistencia de embeddings / referencia en vector store (opcional)."""

    def write_clip_embedding(self, clip_id: str, text_for_embedding: str) -> str | None:
        """Retorna id de vector o ``None`` si no se generó."""


class ClipSemanticMetadataRepositoryPort(Protocol):
    """Persistencia de metadata semántica enriquecida."""

    def upsert_clip_semantic_metadata(self, meta: ClipSemanticMetadata) -> None: ...

    def get_clip_semantic_metadata(self, clip_id: str) -> ClipSemanticMetadata | None: ...


class SceneAnalysisRepositoryPort(Protocol):
    """Persistencia de análisis por escena (narrativa, emoción, intents)."""

    def save_narrative(self, scene_id: str, result: NarrativeClassificationResult, provider: str) -> None: ...

    def save_emotion(self, scene_id: str, analysis: EmotionAnalysis) -> None: ...

    def save_visual_intents(self, scene_id: str, intents: tuple[VisualIntent, ...]) -> None: ...


class FeedbackEventRepositoryPort(Protocol):
    """Almacén de eventos de feedback."""

    def append_event(self, event: FeedbackEvent) -> None: ...


class RankingHistoryRepositoryPort(Protocol):
    """Traza de ranking para observabilidad y reranking."""

    def append_ranking(
        self,
        *,
        clip_id: str | None,
        scene_id: str | None,
        final_score: float,
        factors: dict[str, float] | None,
        query_fingerprint: str | None = None,
    ) -> None: ...
