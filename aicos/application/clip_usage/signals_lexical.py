"""Proxies léxicos de similitud visual (offline, sin píxeles)."""

from __future__ import annotations

import re

from aicos.domain.clip_usage.entities import VisualDiversitySignals
from aicos.domain.clip_usage.derivations import infer_temporal_shot_bucket

_COLOR_GROUPS: dict[str, frozenset[str]] = {
    "warm": frozenset({"warm", "cálido", "calido", "golden", "dorado", "orange", "naranja", "sepia"}),
    "cool": frozenset({"cool", "frío", "frio", "blue", "azul", "teal", "cyan"}),
    "neutral": frozenset({"neutral", "natural", "daylight", "gris", "grey", "gray"}),
    "high_key": frozenset({"bright", "high", "key", "luminoso", "blanco", "clean"}),
    "low_key": frozenset({"dark", "low", "key", "oscuro", "noir", "shadow"}),
    "neon": frozenset({"neon", "vibrant", "saturated", "saturado", "rgb"}),
}

_MOTION = frozenset(
    {
        "handheld",
        "gimbal",
        "steadicam",
        "tracking",
        "pan",
        "tilt",
        "dolly",
        "motion",
        "movimiento",
        "dynamic",
        "montage",
    }
)
_STATIC = frozenset({"static", "tripod", "locked", "still", "tabletop"})


def _color_family(blob: str) -> str:
    for fam, keys in _COLOR_GROUPS.items():
        if any(k in blob for k in keys):
            return fam
    return "unknown"


def _tok(s: str) -> set[str]:
    raw = re.sub(r"[^\w\sáéíóúñü]", " ", s.lower(), flags=re.UNICODE)
    return {t for t in raw.split() if len(t) > 2}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def compute_visual_diversity_signals(current_blob: str, reference_blob: str) -> VisualDiversitySignals:
    """Compara candidato vs último clip seleccionado (o agregado reciente)."""
    c = (current_blob or "").lower()
    r = (reference_blob or "").lower()
    cf, rf = _color_family(c), _color_family(r)
    if cf == "unknown" or rf == "unknown":
        color_sim = 0.45
    else:
        color_sim = 1.0 if cf == rf else 0.28

    b1, b2 = infer_temporal_shot_bucket(c), infer_temporal_shot_bucket(r)
    shot_sim = 1.0 if b1 == b2 else 0.35

    mc = any(m in c for m in _MOTION)
    mr = any(m in r for m in _MOTION)
    sc = any(m in c for m in _STATIC)
    sr = any(m in r for m in _STATIC)
    if mc and mr:
        motion_sim = 0.92
    elif sc and sr:
        motion_sim = 0.78
    elif mc != mr:
        motion_sim = 0.32
    else:
        motion_sim = 0.55

    tc, tr = _tok(c), _tok(r)
    composition_sim = _jaccard(tc, tr)
    semantic_sim = composition_sim

    return VisualDiversitySignals(
        color_similarity=color_sim,
        shot_similarity=shot_sim,
        motion_similarity=motion_sim,
        composition_similarity=composition_sim,
        semantic_similarity=semantic_sim,
    )


def narrative_concept_overlap_penalty(clip_blob: str, prior_concepts: list[str], *, scale: float) -> float:
    """Penaliza repetición narrativa: mismo concepto con mismo vocabulario visual."""
    if not prior_concepts:
        return 0.0
    union = " ".join(prior_concepts).lower()
    pc = _tok(union)
    cc = _tok(clip_blob)
    overlap = _jaccard(pc, cc)
    return float(scale) * overlap
