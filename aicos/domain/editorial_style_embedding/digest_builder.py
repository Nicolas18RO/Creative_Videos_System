"""Texto canónico del estilo editorial (para embedding semántico) — dominio puro."""

from __future__ import annotations

import hashlib

from aicos.domain.editorial_dataset.entities import EditorialPattern


def build_editorial_style_digest_text(
    *,
    creative_id: str,
    scene_count: int,
    total_duration_sec: float,
    style_tags: tuple[str, ...],
    pattern_summaries: tuple[str, ...],
    signature_tags: tuple[str, ...],
    overlay_tags: tuple[str, ...],
    hook_summary: str,
    rhythm_summary: str,
    narrative_summary: str,
    usage_summary: str,
) -> str:
    """Documento estable y legible por modelo de lenguaje (no IDs crudos solos)."""
    parts = [
        f"[creative]{creative_id}",
        f"[scenes]{scene_count}",
        f"[duration_s]{total_duration_sec:.2f}",
        f"[style_tags]{','.join(style_tags)}",
        f"[signatures]{','.join(signature_tags)}",
        f"[cinematic_overlay]{','.join(overlay_tags)}",
        f"[patterns]{' | '.join(pattern_summaries)}",
        f"[hooks]{hook_summary}",
        f"[rhythm]{rhythm_summary}",
        f"[narrative]{narrative_summary}",
        f"[usage_pressure]{usage_summary}",
    ]
    return "\n".join(parts)


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def summarize_patterns_for_digest(
    patterns: tuple[EditorialPattern, ...], *, max_items: int = 8
) -> tuple[str, ...]:
    out: list[str] = []
    for p in patterns[:max_items]:
        seq = "|".join(p.pattern_sequence)
        out.append(f"{p.pattern_type}:{seq}@{p.frequency:.1f}")
    return tuple(out)
