"""Entidades inmutables del dataset editorial (sin dependencias de infraestructura)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class TimelineScene:
    """Una escena en la línea de tiempo con tiempo, orden y señales visuales/narrativas."""

    scene_index: int
    clip_id: str
    start_time: float
    end_time: float
    duration: float
    transition_type: str
    narrative_role: str
    motion_intensity: float
    visual_energy: float
    camera_type: str
    semantic_tags: tuple[str, ...]
    emotion_tags: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CreativeStyleProfile:
    """Perfil agregado del estilo editorial del creativo."""

    hook_intensity: float
    average_pacing: float
    motion_density: float
    transition_density: float
    narrative_aggressiveness: float
    visual_dynamism: float
    cinematic_style_tags: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class EditorialStyleSignals:
    """Señales derivadas complementarias (curva emocional, fuerza de hook, pacing score)."""

    pacing_score: float
    hook_strength: float
    emotional_curve: tuple[float, ...]
    visual_dynamism: float


@dataclass(frozen=True, slots=True)
class EditorialPattern:
    """Patrón editorial recurrente (secuencia ordenada, no clip aislado)."""

    pattern_id: str
    pattern_type: str
    pattern_sequence: tuple[str, ...]
    frequency: float
    confidence_score: float


@dataclass(frozen=True, slots=True)
class HookDetectionResult:
    """Ventana de hook candidata dentro del primer tramo del creativo."""

    window_start: float
    window_end: float
    hook_strength: float
    reasons: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CreativeTimeline:
    """Creativo editado: audio, vídeo final, escenas ordenadas y perfil de estilo."""

    creative_id: str
    audio_path: str
    final_video_path: str
    timeline_scenes: tuple[TimelineScene, ...]
    style_profile: CreativeStyleProfile
    style_signals: EditorialStyleSignals
    editorial_patterns: tuple[EditorialPattern, ...] = ()
    hook_detection: tuple[HookDetectionResult, ...] = ()
    pattern_engine_report: Any = None
    style_embedding: Any = None
    created_at: datetime | None = None
    dataset_version: int = 1
