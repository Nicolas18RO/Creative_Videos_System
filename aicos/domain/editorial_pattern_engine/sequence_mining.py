"""Minería de secuencias editoriales (n-gramas sobre etiquetas)."""

from __future__ import annotations

import hashlib

from aicos.domain.editorial_dataset.entities import EditorialPattern


def mine_recurrent_sequences(
    labels: tuple[str, ...],
    *,
    n_min: int = 2,
    n_max: int = 4,
    min_count: int = 2,
) -> tuple[EditorialPattern, ...]:
    if len(labels) < n_min:
        return ()

    def _clamp01(x: float) -> float:
        return max(0.0, min(1.0, x))

    patterns: dict[tuple[str, ...], int] = {}
    for n in range(n_min, min(n_max, len(labels)) + 1):
        for i in range(0, len(labels) - n + 1):
            seq = tuple(labels[i : i + n])
            patterns[seq] = patterns.get(seq, 0) + 1

    max_possible = max(len(labels) - 1, 1)
    out: list[EditorialPattern] = []
    for seq, count in patterns.items():
        if count < min_count:
            continue
        pid = hashlib.sha256("|".join(seq).encode("utf-8")).hexdigest()[:16]
        freq = float(count)
        confidence = _clamp01(0.55 + 0.45 * (count / max_possible))
        out.append(
            EditorialPattern(
                pattern_id=f"pat_{pid}",
                pattern_type="recurrent_sequence",
                pattern_sequence=seq,
                frequency=freq,
                confidence_score=confidence,
            )
        )
    out.sort(key=lambda p: (-p.frequency, -p.confidence_score))
    return tuple(out)


def mine_production_aware_sequences(
    enriched_labels: tuple[str, ...],
    *,
    n: int = 3,
    min_count: int = 2,
) -> tuple[EditorialPattern, ...]:
    """Patrones sobre etiquetas compuestas (rol + bucket de fuente)."""
    if len(enriched_labels) < n:
        return ()
    patterns: dict[tuple[str, ...], int] = {}
    for i in range(0, len(enriched_labels) - n + 1):
        seq = tuple(enriched_labels[i : i + n])
        patterns[seq] = patterns.get(seq, 0) + 1
    out: list[EditorialPattern] = []
    for seq, count in patterns.items():
        if count < min_count:
            continue
        pid = hashlib.sha256("prod|".encode("utf-8") + "|".join(seq).encode("utf-8")).hexdigest()[:16]
        out.append(
            EditorialPattern(
                pattern_id=f"ppat_{pid}",
                pattern_type="production_aware_sequence",
                pattern_sequence=seq,
                frequency=float(count),
                confidence_score=min(1.0, 0.5 + 0.1 * count),
            )
        )
    return tuple(sorted(out, key=lambda p: (-p.frequency, -p.confidence_score)))
