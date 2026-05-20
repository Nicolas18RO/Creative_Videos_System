"""Reglas puras de transición y fusión de escenas."""

from __future__ import annotations

from aicos.domain.editorial_review.enums import EditorialSceneReviewStatus


def validate_transition(current: str | None, new: str) -> tuple[bool, str]:
    cur = (current or EditorialSceneReviewStatus.PENDING).lower()
    nxt = (new or "").lower()
    if nxt not in EditorialSceneReviewStatus.ALL:
        return False, "invalid_review_status"
    if cur == EditorialSceneReviewStatus.MERGED and nxt != EditorialSceneReviewStatus.MERGED:
        return False, "merged_scene_immutable"
    if cur == EditorialSceneReviewStatus.ACCEPTED and nxt == EditorialSceneReviewStatus.PENDING:
        return False, "accepted_scene_cannot_be_pending"
    return True, ""


def cannot_merge_rejected_scene(status: str) -> bool:
    return (status or "").lower() == EditorialSceneReviewStatus.REJECTED


def merge_requires_adjacent_scenes(scene_index_a: int, scene_index_b: int) -> bool:
    """Compat: índices numéricos consecutivos (tests legacy)."""
    return abs(int(scene_index_a) - int(scene_index_b)) == 1


def scenes_adjacent_in_ordered_list(ordered_scene_indices: tuple[int, ...], scene_index_a: int, scene_index_b: int) -> bool:
    """True si A y B son vecinos en la lista activa ordenada del timeline."""
    if scene_index_a not in ordered_scene_indices or scene_index_b not in ordered_scene_indices:
        return False
    positions = list(ordered_scene_indices)
    pa = positions.index(int(scene_index_a))
    pb = positions.index(int(scene_index_b))
    return abs(pa - pb) == 1


def accepted_scene_cannot_be_pending(status: str) -> bool:
    return (status or "").lower() == EditorialSceneReviewStatus.ACCEPTED
