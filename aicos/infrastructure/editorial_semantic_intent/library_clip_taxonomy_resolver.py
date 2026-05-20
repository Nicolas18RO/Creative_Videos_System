"""Resuelve taxonomía de carpeta desde la biblioteca de clips."""

from __future__ import annotations

from typing import Any

from aicos.application.editorial_semantic_intent.ports import ClipSourceTaxonomyResolverPort
from aicos.domain.editorial_taxonomy.rules import normalize_clip_source_taxonomy
from aicos.services import library_service


class LibraryClipTaxonomyResolver(ClipSourceTaxonomyResolverPort):
    def resolve_clip_source_taxonomy(self, session: Any, clip_id: str) -> str:
        cid = (clip_id or "").strip()
        if not cid or cid.startswith("unassigned_"):
            return "NATURAL"
        row = library_service.get_clip_by_id(session, cid)
        if row is None or not row.narrative_function:
            return "NATURAL"
        return normalize_clip_source_taxonomy(row.narrative_function)
