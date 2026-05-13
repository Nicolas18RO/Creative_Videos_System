"""Entidad pura de contexto global."""

from __future__ import annotations

from dataclasses import dataclass, field

from aicos.domain.context.enums import ContextIntent, IndustryType, NarrativeArc, VisualStyle


@dataclass(frozen=True, slots=True)
class GlobalContextValidation:
    """Resultado de validaciones (flags no mutables)."""

    flags: frozenset[str] = field(default_factory=frozenset)
    notes: str = ""


@dataclass(frozen=True, slots=True)
class GlobalContext:
    """Contexto narrativo global persistible para todo el proyecto de audio."""

    id: str
    project_id: str | None
    topic: str
    industry: IndustryType
    semantic_entities: tuple[str, ...]
    dominant_emotion: str
    narrative_arc: NarrativeArc
    visual_style: VisualStyle
    semantic_anchors: tuple[str, ...]
    content_intent: ContextIntent
    cinematic_context: str
    product_context: str
    continuity_context: str
    validation: GlobalContextValidation = field(default_factory=GlobalContextValidation)
    secondary_industries: tuple[IndustryType, ...] = ()
    embedding_vector_id: str | None = None
    transcript_fingerprint: str = ""
