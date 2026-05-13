"""Global Context Engine — casos de uso y proveedores."""

from aicos.application.context.global_context_service import GlobalContextService
from aicos.application.context.query_enrichment import build_global_query_enrichment
from aicos.application.context.rule_based_global_context_provider import (
    RuleBasedGlobalContextProvider,
    RuleBasedNarrativeInferenceProvider,
)

__all__ = [
    "GlobalContextService",
    "RuleBasedGlobalContextProvider",
    "RuleBasedNarrativeInferenceProvider",
    "build_global_query_enrichment",
]
