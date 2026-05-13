"""Heurísticas NLP y plantillas locales (sin APIs de terceros)."""

from aicos.core.local_ai.concept_local import extract_concept_local
from aicos.core.local_ai.gap_local import (
    generate_image_prompt_local,
    generate_motion_prompt_local,
    generate_tiktok_keywords_local,
)

__all__ = [
    "extract_concept_local",
    "generate_image_prompt_local",
    "generate_motion_prompt_local",
    "generate_tiktok_keywords_local",
]
