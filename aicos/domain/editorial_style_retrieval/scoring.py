"""Métricas de similitud (dominio puro)."""

from __future__ import annotations

import math


def cosine_similarity(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na <= 0 or nb <= 0:
        return 0.0
    return max(0.0, min(1.0, dot / (na * nb)))


def hybrid_similarity_score(
    structural_sim: float,
    semantic_sim: float | None,
    *,
    weight_structural: float,
    weight_semantic: float,
) -> float:
    if semantic_sim is None:
        return max(0.0, min(1.0, structural_sim))
    ws = max(0.0, weight_structural)
    we = max(0.0, weight_semantic)
    s = ws + we
    if s <= 0:
        return structural_sim
    return max(0.0, min(1.0, (ws * structural_sim + we * semantic_sim) / s))
