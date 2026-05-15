"""Métricas de cohesión temporal derivadas de fuentes en el timeline (dominio puro)."""

from __future__ import annotations

import math
from collections import Counter


def timeline_source_entropy(source_ids: tuple[str, ...]) -> float:
    """Entropía normalizada (0–1) de la distribución de source_video_id no vacíos."""
    ids = tuple(s for s in source_ids if (s or "").strip())
    if not ids:
        return 0.0
    counts = Counter(ids)
    total = len(ids)
    h = 0.0
    for c in counts.values():
        p = c / total
        h -= p * math.log(p + 1e-12, 2)
    max_h = math.log(len(counts), 2) if len(counts) > 1 else 1.0
    return max(0.0, min(1.0, h / max(max_h, 1e-6)))


def max_cluster_streak(cluster_ids: tuple[str, ...]) -> int:
    ids = [c for c in cluster_ids if (c or "").strip()]
    if not ids:
        return 0
    run = max_run = 1
    for i in range(1, len(ids)):
        if ids[i] == ids[i - 1]:
            run += 1
            max_run = max(max_run, run)
        else:
            run = 1
    return max_run
