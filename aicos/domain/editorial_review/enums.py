"""Estados de revisión por escena (dominio puro)."""

from __future__ import annotations


class EditorialSceneReviewStatus:
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    MERGED = "merged"
    EDITED = "edited"

    ALL = (PENDING, ACCEPTED, REJECTED, MERGED, EDITED)
