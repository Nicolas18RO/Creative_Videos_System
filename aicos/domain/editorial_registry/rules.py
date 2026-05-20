"""Reglas puras del registry de sesiones editoriales."""

from __future__ import annotations

from aicos.domain.editorial_registry.entities import EditorialRegistrySession
from aicos.domain.editorial_training.entities import EditorialTrainingSessionStatus

REGISTRY_VISIBLE_STATUSES = (
    EditorialTrainingSessionStatus.COMMITTED,
    EditorialTrainingSessionStatus.AWAITING_HUMAN,
    EditorialTrainingSessionStatus.ANALYZING,
    EditorialTrainingSessionStatus.FAILED,
    EditorialTrainingSessionStatus.DRAFT,
    EditorialTrainingSessionStatus.READY,
)


def normalize_status_filter(status: str | None) -> str | None:
    if status is None:
        return None
    s = status.strip().lower()
    if not s or s == "all":
        return None
    if s not in REGISTRY_VISIBLE_STATUSES:
        return None
    return s


def committed_at_for_status(status: str, updated_at) -> bool:
    return (status or "").lower() == EditorialTrainingSessionStatus.COMMITTED


def detect_possible_duplicate(
    entries: tuple[EditorialRegistrySession, ...],
    *,
    creative_id: str,
    creative_label: str,
) -> tuple[EditorialRegistrySession, ...]:
    """Devuelve sesiones que podrían duplicar el creativo (mismo id o etiqueta normalizada)."""
    cid = (creative_id or "").strip().lower()
    label = _normalize_label(creative_label)
    if not cid and not label:
        return ()
    matches: list[EditorialRegistrySession] = []
    for e in entries:
        if cid and e.creative_id.strip().lower() == cid:
            matches.append(e)
            continue
        if label and _normalize_label(e.creative_label) == label:
            matches.append(e)
    return tuple(matches)


def _normalize_label(value: str) -> str:
    return " ".join((value or "").strip().lower().split())


def sort_registry_entries(
    entries: tuple[EditorialRegistrySession, ...],
    *,
    committed_first: bool = True,
) -> tuple[EditorialRegistrySession, ...]:
    def key(e: EditorialRegistrySession) -> tuple:
        committed_rank = 0 if e.status == EditorialTrainingSessionStatus.COMMITTED else 1
        if not committed_first:
            committed_rank = 0
        ts = e.committed_at or e.updated_at
        return (committed_rank, -ts.timestamp())

    return tuple(sorted(entries, key=key))
