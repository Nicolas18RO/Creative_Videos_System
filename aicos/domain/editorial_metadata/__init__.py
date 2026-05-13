"""Dominio editorial: metadata humana y señales de feedback (Fase 5.3)."""

from aicos.domain.editorial_metadata.entities import (
    EditorialCorrection,
    EditorialFeedbackSignal,
    EditorialMetadataRecord,
)
from aicos.domain.editorial_metadata.rules import (
    apply_editorial_override,
    calculate_editorial_quality_score,
    normalize_editorial_tags,
    utc_now,
    validate_editorial_cluster,
)

__all__ = [
    "EditorialCorrection",
    "EditorialFeedbackSignal",
    "EditorialMetadataRecord",
    "apply_editorial_override",
    "calculate_editorial_quality_score",
    "normalize_editorial_tags",
    "utc_now",
    "validate_editorial_cluster",
]
