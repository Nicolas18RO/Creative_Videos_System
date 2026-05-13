"""Derivaciones deterministas de IDs de agrupación (sin I/O ni APIs)."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path


def derive_source_video_id(absolute_path: str, relative_path: str = "") -> str:
    """Agrupa clips que comparten carpeta de biblioteca como proxy de «mismo origen».

    Los clips exportados del mismo master suelen vivir bajo el mismo directorio.
    """
    raw = folder_fallback_hash_for_path(absolute_path, relative_path)
    return raw


def folder_fallback_hash_for_path(absolute_path: str, relative_path: str = "") -> str:
    p = (absolute_path or "").strip()
    if p:
        try:
            parent = Path(p).resolve().parent.as_posix().lower()
        except OSError:
            parent = Path(p).parent.as_posix().lower()
    else:
        parent = ""
    rel = (relative_path or "").strip().replace("\\", "/").lower()
    if not parent and rel:
        parent = str(Path(rel).parent.as_posix())
    raw = parent or rel or "unknown_source"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]


def _norm_tokens(text: str) -> list[str]:
    raw = re.sub(r"[^\w\sáéíóúñü]", " ", (text or "").lower(), flags=re.UNICODE)
    return sorted({t for t in raw.split() if len(t) > 2})


def derive_visual_cluster_id(
    *,
    clip_id: str,
    subcategory: str | None,
    context: str | None,
    semantic_text: str | None,
    absolute_path: str = "",
) -> str:
    """Cluster visual léxico: mismo subcontexto + vocabulario estable = pseudo-mismo plano."""
    sub = (subcategory or "").strip().lower()[:64]
    ctx = (context or "").strip().lower()[:64]
    toks = _norm_tokens(f"{semantic_text or ''} {(subcategory or '')} {(context or '')}")[:24]
    bucket = "|".join([sub, ctx, ",".join(toks)])
    if not bucket.strip("|,"):
        fallback = (clip_id or "")[:8] + (absolute_path or "")[-32:]
        bucket = f"fallback|{fallback}"
    return hashlib.sha256(bucket.encode("utf-8")).hexdigest()[:18]


_SHOT_KEYS: tuple[tuple[str, frozenset[str]], ...] = (
    (
        "closeup",
        frozenset(
            {
                "closeup",
                "close-up",
                "macro",
                "detail",
                "detalle",
                "extreme",
                "cu",
                "primer plano",
            }
        ),
    ),
    (
        "wide",
        frozenset(
            {
                "wide",
                "aerial",
                "drone",
                "establishing",
                "paisaje",
                "landscape",
                "exterior",
                "highway",
            }
        ),
    ),
    (
        "mechanic",
        frozenset(
            {
                "mechanic",
                "mecanico",
                "mecánico",
                "taller",
                "garage",
                "repair",
                "repar",
                "wrench",
            }
        ),
    ),
    (
        "driving",
        frozenset(
            {
                "driving",
                "condu",
                "dashboard",
                "interior",
                "cabin",
                "steering",
                "volante",
                "road",
                "carretera",
            }
        ),
    ),
    (
        "exhaust",
        frozenset(
            {
                "exhaust",
                "escape",
                "tailpipe",
                "emission",
                "fumes",
            }
        ),
    ),
    (
        "engine",
        frozenset(
            {
                "engine",
                "motor",
                "piston",
                "cylinder",
                "block",
                "oil",
                "aceite",
                "lubric",
            }
        ),
    ),
    (
        "smoke",
        frozenset(
            {
                "smoke",
                "humo",
                "vapor",
                "steam",
            }
        ),
    ),
)


def infer_temporal_shot_bucket(blob: str) -> str:
    """Bucket de «plan» / motivo visual para alternancia temporal (proxy léxico)."""
    b = (blob or "").lower()
    for label, keys in _SHOT_KEYS:
        if any(k in b for k in keys):
            return label
    return "general"
