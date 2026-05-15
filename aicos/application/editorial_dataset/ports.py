"""Puertos (protocolos) — application define contratos; infraestructura implementa."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from aicos.domain.editorial_dataset.entities import CreativeTimeline, EditorialPattern, TimelineScene


@dataclass(frozen=True, slots=True)
class VideoProbeResult:
    """Metadatos mínimos de vídeo/audio (sin acoplar a FFmpeg en dominio/aplicación)."""

    duration_ms: int
    width: int | None
    height: int | None


@runtime_checkable
class VideoMetadataProbePort(Protocol):
    def probe_media(self, path: Path) -> VideoProbeResult:
        """Devuelve duración y dimensiones si están disponibles."""


@runtime_checkable
class FilesystemPathPort(Protocol):
    def exists(self, path: Path) -> bool:
        ...

    def resolve(self, path: Path) -> Path:
        ...


@runtime_checkable
class JsonTimelineReadPort(Protocol):
    def load_timeline_document(self, path: Path) -> dict[str, Any]:
        """Carga documento JSON de timeline (estructura acordada con ingest)."""


@dataclass(frozen=True, slots=True)
class RawTimelineSceneInput:
    """DTO de entrada antes de normalización (application boundary)."""

    scene_index: int
    clip_id: str
    start_time: float
    end_time: float
    transition_type: str
    narrative_role: str
    motion_intensity: float
    visual_energy: float
    camera_type: str
    semantic_tags: tuple[str, ...]
    emotion_tags: tuple[str, ...]


@runtime_checkable
class CreativeTimelinePersistenceReadPort(Protocol):
    def get_by_creative_id(self, session: Any, creative_id: str) -> CreativeTimeline | None:
        ...


@runtime_checkable
class CreativeTimelinePersistenceWritePort(Protocol):
    def save(self, session: Any, timeline: CreativeTimeline) -> str:
        """Persiste timeline completo; devuelve id interno de fila."""


@runtime_checkable
class DatasetFileWritePort(Protocol):
    def write_bytes(self, path: Path, data: bytes) -> None:
        ...

    def write_text(self, path: Path, text: str, encoding: str = "utf-8") -> None:
        ...


# Tipos usados solo para anotaciones en servicios
TimelineSceneType = TimelineScene
EditorialPatternType = EditorialPattern
DatetimeOrNone = datetime | None
