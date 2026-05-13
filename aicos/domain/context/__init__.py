"""Dominio: contexto narrativo global (sin dependencias de infraestructura)."""

from aicos.domain.context.entities import GlobalContext, GlobalContextValidation
from aicos.domain.context.enums import ContextIntent, IndustryType, NarrativeArc, VisualStyle

__all__ = [
    "ContextIntent",
    "GlobalContext",
    "GlobalContextValidation",
    "IndustryType",
    "NarrativeArc",
    "VisualStyle",
]
