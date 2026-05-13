"""Entidades de dominio para historial de uso y políticas de reutilización."""

from __future__ import annotations

from dataclasses import dataclass

from aicos.domain.clip_usage.enums import ClipUsageType


@dataclass(frozen=True, slots=True)
class ClipUsageRecord:
    """Una selección (o evento) de clip dentro de una sesión de generación."""

    clip_id: str
    source_video_id: str
    visual_cluster_id: str
    scene_index: int
    timestamp: float
    usage_type: ClipUsageType


@dataclass(frozen=True, slots=True)
class ClipReusePolicy:
    """Política explícita: penalización blanda vs exclusión dura."""

    allow_same_clip: bool = False
    allow_same_source_video: bool = True
    allow_same_visual_cluster: bool = True
    max_reuse_penalty: float = 1.0


@dataclass(frozen=True, slots=True)
class VisualDiversitySignals:
    """Proxies 0..1 de similitud visual/narrativa entre candidato y contexto reciente."""

    color_similarity: float
    shot_similarity: float
    motion_similarity: float
    composition_similarity: float
    semantic_similarity: float
