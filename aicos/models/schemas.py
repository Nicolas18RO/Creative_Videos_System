"""Contratos Pydantic entre capas del AI-COS."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class TranscriptWord(BaseModel):
    """Palabra con tiempo en milisegundos."""

    start_ms: int
    end_ms: int
    word: str


class TranscriptSegment(BaseModel):
    """Segmento de transcript alineado a frase o ventana."""

    start_ms: int
    end_ms: int
    text: str
    words: list[TranscriptWord] = Field(default_factory=list)


class Transcript(BaseModel):
    """Resultado de transcripción (M1)."""

    full_text: str
    language: str
    segments: list[TranscriptSegment]
    duration_ms: int
    audio_path: str


NarrativeFunction = Literal[
    "HOOK",
    "PROBLEM",
    "BENEFIT",
    "RESULT",
    "AUTHORITY",
    "SOCIAL_PROOF",
    "NATURAL",
    "CTA",
]

GenderCode = Literal["F", "M", "N", "MIX", "KIDS"]


class Scene(BaseModel):
    """Escena segmentada del guion."""

    scene_id: str
    scene_index: int
    start_ms: int
    end_ms: int
    duration_ms: int
    text: str
    concept: str = ""
    narrative_function: str = "PROBLEM"
    is_hook: bool = False
    hook_score: float = 0.0
    gender_hint: str | None = None
    project_id: str | None = None
    global_context_id: str | None = None
    global_query_enrichment: str | None = Field(default=None, exclude=True)


class TaxonomyResult(BaseModel):
    """Salida del parser de filenames."""

    gender: str | None = None
    narrative_function: str | None = None
    subcategory: str | None = None
    context: str | None = None
    variant_number: int | None = None
    is_ai_generated: bool = False
    is_naming_compliant: bool = False
    raw_parts: list[str] = Field(default_factory=list)
    asset_kind: Literal["video", "sound_effect", "unknown"] = "video"


class ClipRecord(BaseModel):
    """Registro de clip para API y servicios."""

    id: str
    filename: str
    relative_path: str
    absolute_path: str
    gender: str | None = None
    narrative_function: str | None = None
    subcategory: str | None = None
    context: str | None = None
    variant_number: int | None = None
    is_ai_generated: bool = False
    semantic_text: str = ""
    naming_compliant: bool = True
    needs_reclassification: bool = False
    duration_ms: int | None = None
    resolution_width: int | None = None
    resolution_height: int | None = None
    file_size_bytes: int | None = None
    file_hash: str | None = None
    embedding_id: str | None = None
    thumbnail_path: str | None = None


class ClipSummary(BaseModel):
    """Metadatos ligeros de clip para exploración de biblioteca (sin embeddings)."""

    clip_id: str
    name: str = Field(description="Nombre de archivo del clip")
    relative_path: str = ""
    file_hash: str | None = None
    scene_id: str | None = Field(
        default=None,
        description="Escena de proyecto que tiene este clip como seleccionado, si existe",
    )
    duration_ms: int | None = None
    tags: str | None = None
    narrative_function: str | None = None
    subcategory: str | None = None
    semantic_excerpt: str | None = Field(
        default=None,
        description="Extracto de semantic_text para UI y semillas de búsqueda",
    )
    created_at: str | None = Field(
        default=None,
        description="Reservado; la tabla clips no persiste created_at en el MVP"
    )


class LibraryClipsResponse(BaseModel):
    """Página paginada de clips para GET /library/clips."""

    total: int
    limit: int
    offset: int
    items: list[ClipSummary] = Field(default_factory=list)


class SearchResult(BaseModel):
    """Candidato de búsqueda vectorial + metadatos."""

    clip: ClipRecord
    similarity_score: float
    taxonomy_boost: float = 0.0
    final_score: float = 0.0


class Recommendation(BaseModel):
    """Recomendación rankeada para una escena."""

    clip_id: str
    clip_path: str
    rank: int
    similarity_score: float
    taxonomy_boost: float
    intelligence_boost: float = 0.0
    final_score: float
    narrative_function: str | None = None
    gender: str | None = None
    thumbnail_path: str | None = None
    variants_in_subcategory: int = 0
    clip_subcategory: str | None = Field(default=None, exclude=True)
    clip_context: str | None = Field(default=None, exclude=True)
    clip_semantic_text: str | None = Field(default=None, exclude=True)
    cm_source_video_id: str | None = Field(default=None, exclude=True, description="Origen canónico (Chroma/SQLite).")
    cm_visual_cluster_id: str | None = Field(default=None, exclude=True, description="Cluster visual resuelto.")
    cm_cluster_explicit: str | None = Field(default=None, exclude=True, description="Cluster editorial explícito.")
    cm_visual_embedding_fp: str | None = Field(default=None, exclude=True, description="Huella de embedding visual.")
    cm_master_reel_id: str | None = Field(default=None, exclude=True)
    cm_embedding_model: str | None = Field(default=None, exclude=True)
    cm_visual_collection: str | None = Field(default=None, exclude=True, description="Colección visual editorial.")
    visual_similarity_score: float = Field(
        default=0.0,
        exclude=True,
        description="Sub-score de similitud visual (0..1) para auditoría y Fase 5.2.",
    )
    em_quality_score: float | None = Field(default=None, exclude=True, description="Calidad editorial (SQLite).")
    em_cinematic_score: float | None = Field(default=None, exclude=True, description="Score cinematográfico editorial.")
    em_editorial_tags: str | None = Field(default=None, exclude=True, description="Tags editoriales persistidos.")


class Gap(BaseModel):
    """Escena sin match adecuado (M3)."""

    scene_id: str
    concept: str
    narrative_function: str
    gap_type: Literal["tiktok_search", "ai_generation", "both"]
    tiktok_keywords: list[str] = Field(default_factory=list)
    ai_image_prompt: str | None = None
    ai_motion_prompt: str | None = None
    taxonomy_suggestion: str = ""


class Project(BaseModel):
    """Proyecto de creativo."""

    id: str
    name: str
    product_name: str | None = None
    product_category: str | None = None
    audio_file_path: str | None = None
    status: str = "draft"


class ProjectAnalysis(BaseModel):
    """Salida agregada del analizador de guion."""

    project_id: str
    scenes: list[Scene]
    total_duration_ms: int
    hook_count: int
    total_scenes: int


class SearchRankingContext(BaseModel):
    """Contexto global + escena para ranking híbrido (Contextual Retrieval Engine)."""

    industry: str | None = None
    topic: str | None = None
    dominant_emotion: str | None = None
    semantic_anchors: list[str] = Field(default_factory=list)
    narrative_arc: str | None = None
    visual_style: str | None = None
    content_intent: str | None = None
    scene_text: str | None = None
    scene_concept: str | None = None
    narrative_function: str | None = None
    previous_selected_clip_ids: list[str] = Field(default_factory=list)
    prior_scene_concepts: list[str] = Field(default_factory=list)


class ClipUsageRecordSchema(BaseModel):
    """Registro de uso de clip en una sesión de generación (Fase 4, serializable)."""

    clip_id: str
    source_video_id: str = ""
    visual_cluster_id: str = ""
    scene_index: int = 0
    timestamp: float = 0.0
    usage_type: Literal["selection", "candidate_pool", "rejection", "preview"] = "selection"
    clip_fingerprint: str = Field(
        default="",
        description="Huella léxica del clip al momento de la selección (diversidad vs candidatos siguientes).",
    )


class SearchRunContext(BaseModel):
    """Metadatos opcionales para trazar búsquedas (p. ej. flujo ``analyze_audio``)."""

    source: Literal["api", "audio"] = "api"
    correlation_id: str | None = Field(
        default=None,
        description="UUID de correlación (p. ej. project_id provisional durante el análisis).",
    )
    scene_index: int | None = None
    concept: str | None = Field(default=None, description="Concepto de escena usado como query semántica.")
    ranking_context: SearchRankingContext | None = None
    global_context: GlobalContextSummary | None = Field(
        default=None,
        description="Resumen global (Fase 3 memoria narrativa + coherencia de sesión).",
    )
    clip_usage_records: list[ClipUsageRecordSchema] = Field(
        default_factory=list,
        description="Historial de la sesión de análisis para anti-repetición (Fase 4).",
    )


class NarrativeSceneWindowEntry(BaseModel):
    """Una escena dentro de la ventana deslizante de memoria narrativa."""

    scene_index: int
    clip_id: str
    concept_keywords: list[str] = Field(default_factory=list)
    emotion_token: str = ""
    visual_style_token: str = ""
    pacing_token: str = ""
    camera_token: str = ""
    environment_token: str = ""
    color_token: str = ""
    semantic_fragment: str = ""


class ContinuityVisualBreakdown(BaseModel):
    """Sub-scores de continuidad visual/narrativa (0..1, heurísticos offline)."""

    color_similarity: float = 0.5
    pacing_compatibility: float = 0.5
    camera_movement_compatibility: float = 0.5
    environment_consistency: float = 0.5
    object_persistence: float = 0.5
    emotional_continuity: float = 0.5


class NarrativeMemoryState(BaseModel):
    """Estado serializable de la memoria narrativa por sesión de análisis."""

    session_correlation_id: str
    narrative_session_db_id: str = ""
    previous_selected_clips: list[str] = Field(default_factory=list)
    sliding_window: list[NarrativeSceneWindowEntry] = Field(default_factory=list)
    recent_visual_entities: list[str] = Field(default_factory=list)
    dominant_industry: str = "general"
    dominant_emotion: str = "neutral"
    active_visual_style: str = "unknown"
    narrative_flow: str = "unknown"
    cinematic_energy: float = 0.5
    continuity_constraints: list[str] = Field(default_factory=list)
    industry_lock_active: bool = False
    locked_opening_narrative_arc: str | None = None
    last_narrative_functions: list[str] = Field(default_factory=list)


class SearchRequest(BaseModel):
    """Petición de búsqueda semántica."""

    query: str
    narrative_function: str | None = None
    gender_hint: str | None = None
    is_hook: bool = False
    used_clip_ids: list[str] = Field(default_factory=list)
    n_results: int = 5
    candidate_pool_size: int = 15
    record_usage: bool = Field(
        default=True,
        description="Si false, no persiste eventos de búsqueda (p. ej. benchmarks).",
    )
    apply_intelligence: bool = Field(
        default=True,
        description="Si false, ranking solo vectorial + taxonomía (baseline).",
    )
    global_query_enrichment: str | None = Field(
        default=None,
        description="Prefijo semántico del Global Context Engine (no expuesto al catálogo legacy).",
    )
    reference_visual_fingerprint: str | None = Field(
        default=None,
        description="Huella visual de referencia (p. ej. clip previo) para similitud en ranking híbrido.",
    )
    reference_visual_cluster_id: str | None = Field(
        default=None,
        description="Cluster visual de referencia para continuidad / diversidad.",
    )


class SearchResponse(BaseModel):
    """Respuesta de búsqueda."""

    results: list[Recommendation]
    is_gap: bool = False
    query_fingerprint: str | None = Field(
        default=None,
        description="Huella determinista de la consulta usada para memoria de uso.",
    )


class AnalyzedScene(BaseModel):
    """Escena con recomendaciones M2 y gap M3 opcional."""

    scene: Scene
    recommendations: list[Recommendation] = Field(default_factory=list)
    is_gap: bool = True
    gap: Gap | None = None


class GlobalContextSummary(BaseModel):
    """Contexto narrativo global serializable (API y persistencia)."""

    topic: str = ""
    industry: str = "general"
    semantic_entities: list[str] = Field(default_factory=list)
    dominant_emotion: str = "neutral"
    narrative_arc: str = "unknown"
    visual_style: str = "unknown"
    semantic_anchors: list[str] = Field(default_factory=list)
    content_intent: str = "unknown"
    cinematic_context: str = ""
    product_context: str = ""
    continuity_context: str = ""
    validation_flags: list[str] = Field(default_factory=list)
    validation_notes: str = ""
    secondary_industries: list[str] = Field(default_factory=list)
    embedding_vector_id: str | None = None
    transcript_fingerprint: str = ""


class AnalyzeAPIResponse(BaseModel):
    """Resultado completo del análisis de un MP3 (M1+M2+M3)."""

    project_id: str
    project_name: str = "Proyecto"
    transcript: Transcript
    total_duration_ms: int
    hook_count: int = 0
    scenes: list[AnalyzedScene]
    warning: str | None = None
    global_context_id: str | None = None
    global_context: GlobalContextSummary | None = None
    global_context_embedding_vector: list[float] | None = Field(
        default=None,
        exclude=True,
        description="Solo persistencia SQLite; no se serializa en JSON de API.",
    )


class AnalyzeRequestBody(BaseModel):
    """Cuerpo JSON para `POST /analyze` (ruta local al audio)."""

    audio_path: str
    project_name: str = "Proyecto"
    product_name: str | None = None
    product_category: str = "salud/bienestar"
    target_audience: str = "adultos 35-55"
    gender_hint_default: str | None = None
    include_clip_search: bool = True
    persist: bool = True
    enable_intelligence: bool = Field(
        default=True,
        description="Si true, búsqueda por escena vía search_service + memoria; si false, clip_recommender legacy.",
    )


class GapListItem(BaseModel):
    """Gap con índice de escena para listados."""

    scene_index: int
    gap: Gap


class ProjectGapsResponse(BaseModel):
    """Respuesta de `GET /gaps/{project_id}`."""

    project_id: str
    project_name: str | None = None
    gaps: list[GapListItem]


class VisionClassification(BaseModel):
    """Resultado JSON de clasificación por visión (M4)."""

    gender: str
    narrative_function: str
    subcategory: str
    context: str | None = None
    is_ai_generated: bool = False
    suggested_filename: str
    suggested_folder: str
    confidence: float = 0.0
    tags: list[str] = Field(default_factory=list)


class OrganizeRequestBody(BaseModel):
    """Petición para clasificar (y opcionalmente mover) un clip en `incoming/`."""

    video_path: str
    apply: bool = False


class OrganizeAPIResponse(BaseModel):
    """Salida del organizador M4."""

    classification: VisionClassification
    confidence_threshold: float
    applied: bool
    destination_path: str | None = None
    indexed: bool = False
    message: str | None = None


class FeedbackRequest(BaseModel):
    """Marca una recomendación como aceptada o rechazada (base para Fase 3)."""

    scene_id: str
    clip_id: str
    accepted: bool
    rank: int | None = None


class FeedbackResponse(BaseModel):
    """Resultado de actualizar feedback."""

    updated: int
    scene_id: str
    clip_id: str


class ProjectSummary(BaseModel):
    """Proyecto persistido (lista UI)."""

    id: str
    name: str
    status: str
    audio_file_path: str | None = None
    created_at: str | None = None


class RecommendationDetail(BaseModel):
    """Recomendación con ruta de thumbnail resuelta desde la tabla `clips`."""

    id: str
    clip_id: str
    clip_path: str
    rank: int
    similarity_score: float
    final_score: float
    accepted: bool | None = None
    thumbnail_path: str | None = None


class SceneDetailOut(BaseModel):
    """Escena con recomendaciones para el panel."""

    scene_id: str
    scene_index: int
    text: str
    concept: str
    narrative_function: str
    is_hook: bool
    gender_hint: str | None = None
    recommendations: list[RecommendationDetail] = Field(default_factory=list)


class ProjectDetailResponse(BaseModel):
    """Detalle de proyecto para PyQt6 / API."""

    project: ProjectSummary
    scenes: list[SceneDetailOut] = Field(default_factory=list)


# --- Fase 3: Intelligence / Insights (contratos API) ---


class DistributionAnomaly(BaseModel):
    """Posible anomalía en la distribución de clips (solo metadatos)."""

    kind: str
    detail: str
    severity: Literal["low", "medium", "high"]


class DatasetCoverageInsights(BaseModel):
    """Cobertura del dataset frente al catálogo taxonómico conocido."""

    total_clips: int
    distinct_subcategories: int
    known_subcategory_catalog_size: int
    known_subcategories_represented: int
    coverage_ratio_of_known_catalog: float
    underrepresented_known_subcategories_le_1_clip: int


class WeakTaxonomyCluster(BaseModel):
    """Función narrativa con pocos clips frente a la media del conjunto."""

    narrative_function: str
    clip_count: int
    z_score_vs_mean: float


class TaxonomyBalanceInsights(BaseModel):
    """Equilibrio de funciones narrativas en la biblioteca."""

    narrative_function_counts: dict[str, int]
    balance_score: float
    coefficient_of_variation: float
    weak_taxonomy_clusters: list[WeakTaxonomyCluster] = Field(default_factory=list)


class EmbeddingDistributionSummary(BaseModel):
    """Resumen del índice vectorial vs SQLite (sin leer vectores)."""

    sqlite_clip_count: int
    chroma_indexed_count: int | None = None
    sync_ratio: float | None = None
    collection_name: str
    configured_embedding_dimensions: int


class InsightsSummaryResponse(BaseModel):
    """GET /insights/summary — salud del sistema y cobertura."""

    system_health_score: float
    dataset_coverage: DatasetCoverageInsights
    taxonomy_balance: TaxonomyBalanceInsights
    embedding_distribution_summary: EmbeddingDistributionSummary
    clip_distribution_anomalies: list[DistributionAnomaly] = Field(default_factory=list)
    audio_derived_signals: dict[str, Any] | None = Field(
        default=None,
        description="Agregados ligeros desde eventos de análisis de audio (usage_events).",
    )


class NFCountPair(BaseModel):
    narrative_function: str
    count: int


class NarrativeGapPattern(BaseModel):
    """Patrón agregado de gaps M3 persistidos."""

    gap_type: str
    count: int
    top_narrative_functions: list[NFCountPair] = Field(default_factory=list)


class MissingSemanticCluster(BaseModel):
    """Área semántica del catálogo con poca o ninguna representación."""

    cluster_label: str
    clip_count: int
    note: str = ""


class WeakRetrievalZone(BaseModel):
    """Zona con muchas recomendaciones #1 de baja similitud (proxy de recuperación débil)."""

    zone_label: str
    scene_hits: int
    narrative_function: str


class SearchFailurePattern(BaseModel):
    """Patrón de fallo en búsqueda basado en feedback (rank 1 rechazada)."""

    pattern_label: str
    narrative_function: str
    count: int


class InsightsGapsResponse(BaseModel):
    """GET /insights/gaps — huecos y debilidades de recuperación."""

    narrative_gap_patterns: list[NarrativeGapPattern] = Field(default_factory=list)
    missing_semantic_clusters: list[MissingSemanticCluster] = Field(default_factory=list)
    weak_retrieval_zones: list[WeakRetrievalZone] = Field(default_factory=list)
    search_failure_patterns: list[SearchFailurePattern] = Field(default_factory=list)


class SemanticConceptItem(BaseModel):
    term: str
    count: int


class TrendingClusterItem(BaseModel):
    cluster_id: str
    clip_count: int
    subcategory: str


class InsightsTrendsResponse(BaseModel):
    """GET /insights/trends — tendencias semánticas y taxonómicas."""

    most_frequent_semantic_concepts: list[SemanticConceptItem] = Field(default_factory=list)
    trending_clusters: list[TrendingClusterItem] = Field(default_factory=list)
    narrative_function_distribution: dict[str, int] = Field(default_factory=dict)
    dominant_narrative_pattern: str


# --- Fase 4: AI Decision Layer ---

DecisionType = Literal["optimization", "content", "retrieval"]
DecisionSeverity = Literal["low", "medium", "high"]


class SystemDecision(BaseModel):
    """Decisión estructurada y explicable (sin ML ni re-embeddings)."""

    id: str
    type: DecisionType
    severity: DecisionSeverity
    affected_entities: list[str] = Field(default_factory=list)
    explanation: str
    suggested_action: str
    confidence_score: float = Field(ge=0.0, le=1.0)


class DecisionsSummaryResponse(BaseModel):
    """GET /decisions/summary."""

    system_decision_score: float
    total_active_decisions: int
    high_severity_count: int
    decision_distribution: dict[str, int] = Field(default_factory=dict)


class DecisionsListResponse(BaseModel):
    """GET /decisions/list — paginado."""

    items: list[SystemDecision] = Field(default_factory=list)
    total: int
    limit: int
    offset: int


class ImpactedArea(BaseModel):
    """Área del sistema con más decisiones asociadas."""

    area: str
    decision_count: int
    max_severity: DecisionSeverity


class ClusterInstability(BaseModel):
    """Cluster o eje taxonómico con señales de inestabilidad."""

    cluster_id: str
    instability_score: float
    narrative_function: str | None = None


class CategoryIntervention(BaseModel):
    """Categoría que requiere intervención (cobertura o calidad)."""

    category: str
    reason: str
    related_decision_ids: list[str] = Field(default_factory=list)


class DecisionsImpactResponse(BaseModel):
    """GET /decisions/impact."""

    most_affected_system_areas: list[ImpactedArea] = Field(default_factory=list)
    clusters_highest_instability: list[ClusterInstability] = Field(default_factory=list)
    categories_requiring_intervention: list[CategoryIntervention] = Field(default_factory=list)


# --- Fase 3 PRD: inteligencia de recuperación, hooks, reclasificación, benchmark ---


class HookSearchResultItem(BaseModel):
    clip_id: str
    clip_path: str
    similarity_score: float
    final_score: float
    narrative_function: str | None = None
    thumbnail_path: str | None = None


class HookSearchResponse(BaseModel):
    """GET /hooks/search — recuperación semántica restringida a hooks."""

    query: str
    results: list[HookSearchResultItem] = Field(default_factory=list)
    is_gap: bool = False


class ReclassificationSuggestion(BaseModel):
    clip_id: str
    relative_path: str
    current_narrative_function: str | None = None
    current_subcategory: str | None = None
    filename_parse_gender: str | None = None
    filename_parse_narrative_function: str | None = None
    filename_parse_subcategory: str | None = None
    vision_suggestion: VisionClassification | None = None
    notes: str = ""


class ReclassificationBatchRequest(BaseModel):
    limit: int = Field(12, ge=1, le=40)
    include_export_file: bool = True
    use_db_flagged: bool = True


class ReclassificationBatchResponse(BaseModel):
    suggestions: list[ReclassificationSuggestion] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)


class Phase3BenchmarkResponse(BaseModel):
    """GET /benchmark/phase3 — comparación baseline vs ranking con inteligencia."""

    k: int
    cases_evaluated: int
    baseline_precision_at_k: float
    enhanced_precision_at_k: float
    relative_improvement_percent: float
    mean_reciprocal_rank_baseline: float
    mean_reciprocal_rank_enhanced: float
    prd_milestone_hit_rate_enhanced: bool
    prd_milestone_note: str
    trace: list[str] = Field(default_factory=list)


# --- Diagnóstico pipeline /analyze ---


class AnalyzeHealthCheck(BaseModel):
    """Una comprobación dentro de ``GET /analyze/health``."""

    name: str
    ok: bool
    status: Literal["pass", "fail", "skipped"] = "pass"
    message: str | None = None
    failure_reason: str | None = None
    recoverable: bool = True
    details: dict[str, Any] | None = None


class AnalyzeHealthResponse(BaseModel):
    """Estado agregado de dependencias para análisis de audio."""

    ok: bool
    overall_status: Literal["healthy", "unhealthy"] = "healthy"
    summary: str = ""
    checks: list[AnalyzeHealthCheck] = Field(default_factory=list)
    timestamp: str


# --- Inteligencia cinematográfica (texto → narrativa / emoción / intents) ---


class CinematicSceneTextRequest(BaseModel):
    """POST /cinematic/scene-text — análisis local sin clips."""

    transcript: str = ""
    scene_text: str = ""
    context: str | None = None


class CinematicNarrativeBlock(BaseModel):
    narrative_role: str
    confidence: float
    reasoning: str
    compatible_visual_styles: list[str] = Field(default_factory=list)
    pacing_recommendation: str = "MEDIUM"
    provider_used: str = ""


class CinematicEmotionBlock(BaseModel):
    primary_emotion: str
    secondary_emotions: list[str] = Field(default_factory=list)
    emotional_intensity: float = 0.0
    emotional_arc_position: str = ""
    energy_curve: str = ""
    emotional_transition: str = ""


class CinematicVisualIntentBlock(BaseModel):
    intent_type: str
    cinematic_priority: float = 0.5
    suggested_camera_styles: list[str] = Field(default_factory=list)
    suggested_editing_styles: list[str] = Field(default_factory=list)
    suggested_visual_elements: list[str] = Field(default_factory=list)
    suggested_motion: list[str] = Field(default_factory=list)
    suggested_color_mood: list[str] = Field(default_factory=list)
    suggested_transition_style: list[str] = Field(default_factory=list)
    suggested_shot_types: list[str] = Field(default_factory=list)


class CinematicSceneTextResponse(BaseModel):
    narrative: CinematicNarrativeBlock
    emotion: CinematicEmotionBlock
    visual_intents: list[CinematicVisualIntentBlock] = Field(default_factory=list)


# --- Editorial cinematográfica (Fase 5.3) ---


class EditorialMetadataSchema(BaseModel):
    """Vista API de metadata editorial fusionada."""

    clip_id: str
    source_video_id: str = ""
    master_reel_id: str = ""
    editorial_tags: str = ""
    editorial_notes: str = ""
    narrative_role: str = ""
    emotion_profile: str = ""
    visual_style: str = ""
    cinematic_style: str = ""
    visual_cluster_id: str = ""
    cluster_override: str = ""
    pacing_type: str = ""
    shot_type: str = ""
    quality_score: float | None = None
    cinematic_score: float | None = None
    reviewed: bool = False
    reviewed_by: str = ""
    reviewed_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class EditorialPatchRequest(BaseModel):
    """PATCH parcial; solo campos presentes se actualizan."""

    editorial_tags: str | None = None
    editorial_notes: str | None = None
    visual_cluster_override: str | None = None
    narrative_role: str | None = None
    emotion_profile: str | None = None
    visual_style: str | None = None
    cinematic_style: str | None = None
    pacing_type: str | None = None
    shot_type: str | None = None
    editorial_source_video_id: str | None = None
    editorial_master_reel_id: str | None = None
    quality_score: float | None = None
    cinematic_score: float | None = None
    reviewed: bool | None = None
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None


class EditorialFeedbackCreate(BaseModel):
    """POST feedback editorial humano."""

    clip_id: str
    usefulness_score: float = Field(ge=0.0, le=1.0)
    continuity_score: float = Field(ge=0.0, le=1.0)
    diversity_score: float = Field(ge=0.0, le=1.0)
    narrative_quality: float = Field(ge=0.0, le=1.0)
    visual_quality: float = Field(ge=0.0, le=1.0)
    human_feedback: str = ""


class EditorialFeedbackResponse(BaseModel):
    """Respuesta tras persistir feedback."""

    feedback_id: str
    clip_id: str


class EditorialBulkItem(BaseModel):
    """Un ítem de actualización masiva."""

    clip_id: str
    patch: EditorialPatchRequest


class EditorialBulkUpdateRequest(BaseModel):
    """Actualización masiva (datasets curatoriales)."""

    items: list[EditorialBulkItem] = Field(default_factory=list, max_length=500)
    corrected_by: str = "editor"
    correction_reason: str = "bulk_update"


class EditorialBulkUpdateResponse(BaseModel):
    """Resumen de bulk update."""

    updated: int


class EditorialClusterListResponse(BaseModel):
    """Lista de clips en un cluster (override o explícito)."""

    cluster_id: str
    limit: int
    offset: int
    clips: list[EditorialMetadataSchema] = Field(default_factory=list)
