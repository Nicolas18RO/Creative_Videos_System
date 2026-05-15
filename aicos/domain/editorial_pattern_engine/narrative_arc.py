"""Inferencia de esqueleto narrativo por roles y energía (dominio puro)."""

from __future__ import annotations

import statistics

from aicos.domain.editorial_pattern_engine.entities import NarrativeStructureSketch


def infer_narrative_structure(
    narrative_roles: tuple[str, ...],
    energies: tuple[float, ...],
) -> NarrativeStructureSketch:
    if not narrative_roles:
        return NarrativeStructureSketch(
            phase_labels=(),
            phase_confidence=0.0,
            dominant_structure_name="unknown",
        )
    phases: list[str] = []
    for r in narrative_roles:
        low = r.lower()
        if any(k in low for k in ("hook", "cold_open", "impact", "shock")):
            phases.append("hook")
        elif any(k in low for k in ("problem", "pain", "tension")):
            phases.append("problem")
        elif any(k in low for k in ("proof", "authority", "demo", "mechanic")):
            phases.append("proof")
        elif any(k in low for k in ("benefit", "result", "payoff")):
            phases.append("payoff")
        elif any(k in low for k in ("cta", "close", "outro")):
            phases.append("cta")
        else:
            phases.append("bridge")
    # Confianza: coherencia de progresión energética (subida hacia payoff).
    conf = 0.45
    if energies and len(energies) > 2:
        first = statistics.fmean(energies[: max(1, len(energies) // 4)])
        last = statistics.fmean(energies[-max(1, len(energies) // 4) :])
        if last > first + 0.08:
            conf += 0.25
        if "hook" in phases[:2]:
            conf += 0.15
        if "payoff" in phases[-3:] or "cta" in phases[-2:]:
            conf += 0.15
    conf = max(0.0, min(1.0, conf))
    structure = "classic_arc" if phases[0] == "hook" and "payoff" in phases else "modular_arc"
    return NarrativeStructureSketch(
        phase_labels=tuple(phases),
        phase_confidence=float(conf),
        dominant_structure_name=structure,
    )
