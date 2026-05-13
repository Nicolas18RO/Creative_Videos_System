"""Puertos del Global Context Engine (inversión de dependencias)."""

from __future__ import annotations

from typing import Any, Protocol

from aicos.domain.context.entities import GlobalContext


class ContextAnalyzerPort(Protocol):
    """Extrae tópico, industria, anclas y emoción dominante desde texto completo."""

    def analyze(
        self,
        transcript_text: str,
        *,
        product_category: str | None,
        target_audience: str | None,
    ) -> GlobalContext:
        """Produce un ``GlobalContext`` con ``id`` temporal (vacío) y ``project_id`` None."""


class NarrativeInferencePort(Protocol):
    """Refina arco narrativo (puede sobreescribir heurística del analizador)."""

    def infer_arc(self, transcript_text: str, current: GlobalContext) -> GlobalContext:
        """Retorna copia lógica del contexto con ``narrative_arc`` ajustado."""


class GlobalEmbeddingPort(Protocol):
    """Embedding del bloque semántico global (local u otro proveedor)."""

    def embed_context(self, embedding_text: str) -> tuple[list[float], str]:
        """Retorna (vector, embedding_id determinista o de store)."""


class GlobalContextRepositoryPort(Protocol):
    """Persistencia transaccional (la sesión la abre quien orquesta el commit)."""

    def save(self, session: Any, ctx: GlobalContext, vector: list[float] | None) -> None:
        """Inserta/actualiza ``global_contexts`` y tablas hijas."""
