"""Reglas puras de categoría editorial y prioridad humano > auto."""

from __future__ import annotations

EDITORIAL_NARRATIVE_ROLES: tuple[str, ...] = (
    "HOOK",
    "PROBLEM",
    "BENEFIT",
    "RESULT",
    "AUTHORITY",
    "SOCIAL_PROOF",
    "PRODUCT",
    "CTA",
    "NATURAL",
)


def normalize_narrative_role(role: str | None, *, default: str = "NATURAL") -> str:
    r = (role or "").strip().upper().replace(" ", "_")
    if r in EDITORIAL_NARRATIVE_ROLES:
        return r
    if r == "AUTHORITY":
        return "AUTHORITY"
    return default if not r else r


def effective_narrative_role(auto_role: str, human_role: str | None) -> str:
    """La decisión humana siempre gana si está definida."""
    if human_role and str(human_role).strip():
        return normalize_narrative_role(human_role)
    return normalize_narrative_role(auto_role)


def should_persist_human_override(auto_role: str, proposed_human: str) -> bool:
    """True si el usuario eligió una categoría distinta a la detectada automáticamente."""
    auto = normalize_narrative_role(auto_role)
    human = normalize_narrative_role(proposed_human)
    return human != auto


def auto_role_must_not_be_overwritten(existing_auto: str, incoming_auto: str) -> str:
    """Nunca sobrescribir auto una vez establecido (integridad de auditoría)."""
    if (existing_auto or "").strip():
        return normalize_narrative_role(existing_auto)
    return normalize_narrative_role(incoming_auto)


def scene_type_label_for_role(narrative_role: str) -> str:
    nr = normalize_narrative_role(narrative_role)
    if nr == "HOOK":
        return "Hook Scene"
    if nr == "CTA":
        return "Call To Action"
    if nr == "PRODUCT":
        return "Product Scene"
    if nr:
        return nr.replace("_", " ").title()
    return "Scene"
