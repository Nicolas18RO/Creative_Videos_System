"""Reglas puras de metadata editorial (sin I/O)."""

from __future__ import annotations

import re
from datetime import datetime, timezone


def apply_editorial_override(*, auto_cluster: str, cluster_override: str | None) -> str:
    """Devuelve el cluster efectivo: override editorial gana sobre el automático."""
    o = (cluster_override or "").strip()
    if o:
        return o[:128]
    return (auto_cluster or "").strip()[:128]


def validate_editorial_cluster(value: str | None) -> tuple[bool, str]:
    """Valida identificador de cluster editorial (longitud y caracteres seguros)."""
    if value is None:
        return True, ""
    s = value.strip()
    if len(s) > 128:
        return False, "cluster_too_long"
    if s and not re.match(r"^[A-Za-z0-9_\-./]+$", s):
        return False, "cluster_invalid_chars"
    return True, ""


def normalize_editorial_tags(raw: str | None) -> str:
    """Normaliza tags separados por coma: minúsculas, sin duplicados, orden estable."""
    if not raw or not raw.strip():
        return ""
    parts = [p.strip().lower() for p in raw.split(",") if p.strip()]
    seen: set[str] = set()
    out: list[str] = []
    for p in parts:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return ",".join(out)


def calculate_editorial_quality_score(
    *,
    quality_score: float | None,
    cinematic_score: float | None,
    quality_weight: float = 0.4,
    cinematic_weight: float = 0.6,
) -> float:
    """Combina puntuaciones editoriales en [0,1] (heurística estable)."""
    q = 0.0 if quality_score is None else max(0.0, min(1.0, float(quality_score)))
    c = 0.0 if cinematic_score is None else max(0.0, min(1.0, float(cinematic_score)))
    wq = max(0.0, float(quality_weight))
    wc = max(0.0, float(cinematic_weight))
    denom = wq + wc
    if denom <= 0.0:
        return 0.0
    return max(0.0, min(1.0, (wq * q + wc * c) / denom))


def utc_now() -> datetime:
    """Timestamp consciente de zona (tests mockeables vía reglas locales)."""
    return datetime.now(timezone.utc)
