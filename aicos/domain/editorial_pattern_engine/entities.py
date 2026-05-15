"""Modelo de resultado del motor editorial (sin ORM ni I/O)."""

from __future__ import annotations

from dataclasses import dataclass

from aicos.domain.editorial_dataset.entities import EditorialPattern, HookDetectionResult, TimelineScene


@dataclass(frozen=True, slots=True)
class CinematicClipSlice:
    """Subconjunto de metadatos de producción relevantes para patrones de timeline."""

    source_video_id: str
    master_reel_id: str
    production_group: str
    camera_id: str
    shooting_session_id: str
    visual_cluster_id_explicit: str


@dataclass(frozen=True, slots=True)
class LibraryClipSlice:
    """Taxonomía de biblioteca (Fase 5 implícita vía clips)."""

    narrative_function: str
    subcategory: str
    context: str


@dataclass(frozen=True, slots=True)
class TimelineEnrichmentBundle:
    """Enriquecimiento por clip_id antes de fusionar con escenas."""

    cinematic_by_clip: dict[str, CinematicClipSlice]
    library_by_clip: dict[str, LibraryClipSlice]


@dataclass(frozen=True, slots=True)
class EnrichedSceneFingerprint:
    """Huella timeline-aware: tiempo + orden + producción + taxonomía + energía."""

    scene_index: int
    clip_id: str
    editorial_label: str
    start_time: float
    end_time: float
    duration_sec: float
    transition_type: str
    motion_intensity: float
    visual_energy: float
    camera_type: str
    semantic_tags: tuple[str, ...]
    emotion_tags: tuple[str, ...]
    source_video_id: str
    master_reel_id: str
    production_group: str
    camera_id_production: str
    visual_cluster_explicit: str
    library_narrative_function: str
    library_subcategory: str


@dataclass(frozen=True, slots=True)
class CutBurstWindow:
    """Ráfaga de cortes: intervalo temporal + intensidad relativa."""

    window_start: float
    window_end: float
    burst_intensity: float
    shots_in_window: int


@dataclass(frozen=True, slots=True)
class CutRhythmProfile:
    """Ritmo de plano y micro-pacing de cortes."""

    mean_shot_duration: float
    std_shot_duration: float
    coefficient_of_variation: float
    cuts_per_minute: float
    acceleration_index: float
    burst_windows: tuple[CutBurstWindow, ...]


@dataclass(frozen=True, slots=True)
class MomentumFlowProfile:
    """Momentum visual acumulado y reversals (flow temporal)."""

    momentum_samples: tuple[float, ...]
    mean_momentum: float
    momentum_variance: float
    reversal_count: int
    sustained_high_blocks: int


@dataclass(frozen=True, slots=True)
class NarrativeStructureSketch:
    """Hipótesis de arco narrativo por fases (roles + energía)."""

    phase_labels: tuple[str, ...]
    phase_confidence: float
    dominant_structure_name: str


@dataclass(frozen=True, slots=True)
class PerClipUsagePressure:
    """Presión histórica de uso (Fase 4) sobre un clip presente en el timeline."""

    clip_id: str
    global_selection_count: int
    distinct_sessions: int
    mean_final_score: float


@dataclass(frozen=True, slots=True)
class ClipUsagePressureDigest:
    """Agregado de presión de reutilización para clips del creativo actual."""

    by_clip: tuple[PerClipUsagePressure, ...]
    timeline_source_entropy: float
    max_cluster_streak_length: int


@dataclass(frozen=True, slots=True)
class EditorialPatternEngineReport:
    """Informe completo del motor 6.2 (comportamiento editorial humano)."""

    engine_version: str
    enriched_scenes: tuple[EnrichedSceneFingerprint, ...]
    cut_rhythm: CutRhythmProfile
    momentum: MomentumFlowProfile
    narrative_sketch: NarrativeStructureSketch
    usage_digest: ClipUsagePressureDigest
    hooks: tuple[HookDetectionResult, ...]
    sequence_patterns: tuple[EditorialPattern, ...]
    editorial_signature_tags: tuple[str, ...]
    cinematic_style_overlay: tuple[str, ...]


def merge_scene_with_enrichment(
    scene: TimelineScene,
    *,
    editorial_label: str,
    cine: CinematicClipSlice | None,
    lib: LibraryClipSlice | None,
) -> EnrichedSceneFingerprint:
    c = cine or CinematicClipSlice("", "", "", "", "", "")
    l = lib or LibraryClipSlice("", "", "")
    return EnrichedSceneFingerprint(
        scene_index=scene.scene_index,
        clip_id=scene.clip_id,
        editorial_label=editorial_label,
        start_time=scene.start_time,
        end_time=scene.end_time,
        duration_sec=scene.duration,
        transition_type=scene.transition_type,
        motion_intensity=scene.motion_intensity,
        visual_energy=scene.visual_energy,
        camera_type=scene.camera_type,
        semantic_tags=scene.semantic_tags,
        emotion_tags=scene.emotion_tags,
        source_video_id=(c.source_video_id or "").strip(),
        master_reel_id=(c.master_reel_id or "").strip(),
        production_group=(c.production_group or "").strip(),
        camera_id_production=(c.camera_id or "").strip(),
        visual_cluster_explicit=(c.visual_cluster_id_explicit or "").strip(),
        library_narrative_function=(l.narrative_function or "").strip(),
        library_subcategory=(l.subcategory or "").strip(),
    )
