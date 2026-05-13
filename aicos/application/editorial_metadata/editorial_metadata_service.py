"""Servicio de aplicación: metadata editorial y overrides."""

from __future__ import annotations

import logging
from typing import Any

from aicos.application.editorial_metadata.ports import (
    EditorialMetadataReadPort,
    EditorialMetadataWritePort,
)
from aicos.config import EditorialMetadataConfig
from aicos.domain.editorial_metadata.entities import EditorialCorrection, EditorialMetadataRecord
from aicos.domain.editorial_metadata.rules import (
    normalize_editorial_tags,
    utc_now,
    validate_editorial_cluster,
)

logger = logging.getLogger(__name__)


class EditorialMetadataService:
    """Orquesta lectura/escritura y reglas de negocio editoriales."""

    def __init__(
        self,
        *,
        read_port: EditorialMetadataReadPort,
        write_port: EditorialMetadataWritePort,
        cfg: EditorialMetadataConfig,
    ) -> None:
        self._read = read_port
        self._write = write_port
        self._cfg = cfg

    def get_clip(self, session: Any, clip_id: str) -> EditorialMetadataRecord | None:
        return self._read.get_by_clip_id(session, clip_id)

    def list_clips(self, session: Any, *, offset: int, limit: int) -> list[EditorialMetadataRecord]:
        return self._read.list_paginated(session, offset=offset, limit=limit)

    def search_tags(self, session: Any, *, tag_query: str, limit: int) -> list[EditorialMetadataRecord]:
        return self._read.search_by_tags(session, tag_query=tag_query, limit=limit)

    def list_cluster(self, session: Any, *, cluster_id: str, limit: int, offset: int) -> list[EditorialMetadataRecord]:
        ok, reason = validate_editorial_cluster(cluster_id)
        if not ok:
            raise ValueError(reason)
        return self._read.search_by_cluster(session, cluster_id=cluster_id, limit=limit, offset=offset)

    def patch_clip(
        self,
        session: Any,
        *,
        clip_id: str,
        fields: dict[str, Any],
        corrected_by: str,
        correction_reason: str,
    ) -> EditorialMetadataRecord:
        if not self._cfg.allow_editorial_overrides and any(
            k in fields for k in ("visual_cluster_override", "editorial_source_video_id", "editorial_master_reel_id")
        ):
            raise PermissionError("editorial_overrides_disabled")
        current = self._read.get_by_clip_id(session, clip_id)
        if current is None:
            raise LookupError("clip_not_found")
        if "visual_cluster_override" in fields and fields["visual_cluster_override"] is not None:
            ok, reason = validate_editorial_cluster(str(fields["visual_cluster_override"]))
            if not ok:
                raise ValueError(reason)
        history: list[dict[str, Any]] = []
        now = utc_now()
        if "editorial_tags" in fields and fields["editorial_tags"] is not None:
            fields = {**fields, "editorial_tags": normalize_editorial_tags(str(fields["editorial_tags"]))}
        for key, new_val in fields.items():
            if key not in _PATCHABLE_FIELDS:
                continue
            old = _field_as_str(getattr(current, key, None))
            new_s = _field_as_str(new_val)
            if old == new_s:
                continue
            corr = EditorialCorrection(
                field_name=key,
                previous_value=old,
                corrected_value=new_s,
                correction_reason=correction_reason,
                corrected_by=corrected_by,
                timestamp=now,
            )
            history.append(
                {
                    "field_name": corr.field_name,
                    "previous_value": corr.previous_value,
                    "corrected_value": corr.corrected_value,
                    "correction_reason": corr.correction_reason,
                    "corrected_by": corr.corrected_by,
                    "timestamp": corr.timestamp.isoformat(),
                }
            )
            logger.info(
                "[EditorialOverride] clip=%s field=%s",
                clip_id,
                key,
            )
        self._write.patch(session, clip_id=clip_id, fields=fields, correction_history=history)
        out = self._read.get_by_clip_id(session, clip_id)
        if out is None:
            raise RuntimeError("read_after_patch_failed")
        logger.info("[EditorialMetadata] clip=%s updated=True corrections=%s", clip_id, len(history))
        if (out.cinematic_score is not None and out.cinematic_score >= 0.9) or (
            out.quality_score is not None and out.quality_score >= 0.9
        ):
            logger.info(
                "[EditorialQuality] clip=%s cinematic_score=%s quality_score=%s",
                clip_id,
                out.cinematic_score,
                out.quality_score,
            )
        return out

    def bulk_patch(
        self,
        session: Any,
        *,
        items: list[tuple[str, dict[str, Any]]],
        corrected_by: str,
        correction_reason: str,
    ) -> int:
        if not self._cfg.enable_bulk_operations:
            raise PermissionError("bulk_disabled")
        n = 0
        for clip_id, patch in items:
            try:
                self.patch_clip(
                    session,
                    clip_id=clip_id,
                    fields=patch,
                    corrected_by=corrected_by,
                    correction_reason=correction_reason,
                )
                n += 1
            except LookupError:
                logger.warning("[EditorialMetadata] bulk_skip clip=%s reason=not_found", clip_id)
            except ValueError as e:
                logger.warning("[EditorialMetadata] bulk_skip clip=%s err=%s", clip_id, e)
        logger.info("[EditorialMetadata] bulk_update count=%s", n)
        return n


_PATCHABLE_FIELDS = frozenset(
    {
        "editorial_tags",
        "editorial_notes",
        "visual_cluster_override",
        "narrative_role",
        "emotion_profile",
        "visual_style",
        "cinematic_style",
        "pacing_type",
        "shot_type",
        "editorial_source_video_id",
        "editorial_master_reel_id",
        "quality_score",
        "cinematic_score",
        "reviewed",
        "reviewed_by",
        "reviewed_at",
    }
)


def _field_as_str(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, bool):
        return "1" if v else "0"
    return str(v)
