"""Reglas puras: resolución de IDs canónicos y huellas de embeddings."""

from __future__ import annotations

import hashlib
import math
from typing import Sequence

from aicos.domain.cinematic_metadata.entities import SourceVideoMetadata


def _stable_hash(payload: str, n: int = 20) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:n]


def resolve_source_video_identifier(
    explicit: SourceVideoMetadata | None,
    *,
    folder_fallback_hash: str,
) -> str:
    """Prioriza metadatos explícitos; si no, ``master_reel_id`` estable; si no, hash de carpeta."""
    if explicit is not None:
        sid = (explicit.source_video_id or "").strip()
        if sid:
            return sid[:128]
        mid = (explicit.master_reel_id or "").strip()
        if mid:
            return _stable_hash(f"master_reel|{mid.lower()}", n=22)
    fb = (folder_fallback_hash or "").strip()
    return fb if fb else _stable_hash("unknown_source", n=20)


def fingerprint_visual_embedding(
    vector: Sequence[float],
    *,
    model_tag: str = "",
    max_dims: int = 64,
) -> str:
    """Huella determinista de un vector (para Chroma y clustering laxo, sin almacenar tensor)."""
    if not vector:
        return ""
    n = min(max_dims, len(vector))
    parts = [f"{model_tag}:"] if model_tag else []
    for i in range(n):
        v = float(vector[i])
        q = math.floor(v * 1000.0 + 0.5) / 1000.0
        parts.append(f"{i}:{q:.5f}")
    return _stable_hash("|".join(parts), n=32)


def resolve_visual_cluster_identifier(
    *,
    explicit_cluster_id: str | None,
    visual_embedding_fingerprint: str | None,
    lexical_cluster_id: str,
) -> str:
    """Prioriza cluster explícito, luego huella visual, luego cluster léxico."""
    ec = (explicit_cluster_id or "").strip()
    if ec:
        return ec[:96]
    fp = (visual_embedding_fingerprint or "").strip()
    if fp:
        return f"vfp:{fp[:48]}"
    lx = (lexical_cluster_id or "").strip()
    return lx if lx else _stable_hash("visual_cluster_empty", n=18)
