"""Cálculos puros de similitud visual y fusión híbrida (sin I/O)."""

from __future__ import annotations


def _norm_fp(s: str) -> str:
    return (s or "").strip().lower()


def _prefix_similarity(a: str, b: str) -> float:
    """Similitud 0..1 por prefijo común normalizado (huellas hex/base64 acotadas)."""
    x, y = _norm_fp(a), _norm_fp(b)
    if not x or not y:
        return 0.0
    if x == y:
        return 1.0
    n = min(len(x), len(y))
    if n == 0:
        return 0.0
    common = 0
    for i in range(n):
        if x[i] == y[i]:
            common += 1
        else:
            break
    return common / max(len(x), len(y))


def compute_visual_similarity_components(
    *,
    reference_fingerprint: str,
    reference_cluster_id: str,
    clip_fingerprint: str | None,
    clip_cluster_id: str | None,
) -> tuple[float, float, float]:
    """Devuelve ``(fp_score, cluster_score, blended)`` en [0,1].

    ``blended`` combina huella y cluster con peso a favor de coincidencia exacta de huella.
    """
    fp = _prefix_similarity(reference_fingerprint, clip_fingerprint or "")
    cref = (reference_cluster_id or "").strip()
    cclip = (clip_cluster_id or "").strip()
    if not cref or not cclip:
        cl = 0.0
    elif cref == cclip:
        cl = 1.0
    else:
        cl = _prefix_similarity(cref, cclip) * 0.6
    blended = min(1.0, 0.65 * fp + 0.35 * cl)
    return fp, cl, blended


def compute_hybrid_final_score(
    *,
    semantic_score: float,
    narrative_score: float,
    emotion_score: float,
    continuity_score: float,
    visual_similarity_score: float,
    penalties: float,
    visual_weight: float,
) -> float:
    """Fusión acotada [0,1]; ``visual_weight`` escala solo el término visual."""
    base = (
        float(semantic_score)
        + float(narrative_score)
        + float(emotion_score)
        + float(continuity_score)
        + float(visual_weight) * float(visual_similarity_score)
        - float(penalties)
    )
    if base < 0.0:
        return 0.0
    if base > 1.0:
        return 1.0
    return base
