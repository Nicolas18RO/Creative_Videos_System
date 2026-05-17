"""Puertos del vertical timeline_visualization."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from aicos.domain.timeline_visualization.entities import TimelineClipPreview


@runtime_checkable
class TimelineClipPreviewPersistencePort(Protocol):
    def list_by_creative_id(self, session: Any, creative_id: str) -> tuple[TimelineClipPreview, ...]:
        ...

    def upsert_batch(self, session: Any, creative_id: str, previews: tuple[TimelineClipPreview, ...]) -> None:
        ...

    def delete_by_creative_id(self, session: Any, creative_id: str) -> None:
        ...


@runtime_checkable
class TimelineMediaGenerationPort(Protocol):
    def ensure_scene_thumbnail(
        self,
        *,
        source_video: Path,
        creative_id: str,
        scene_index: int,
        start_time: float,
        end_time: float,
    ) -> Path | None:
        ...

    def ensure_scene_preview(
        self,
        *,
        source_video: Path,
        creative_id: str,
        scene_index: int,
        start_time: float,
        end_time: float,
    ) -> Path | None:
        ...

    def purge_creative_cache(self, creative_id: str) -> None:
        ...


@runtime_checkable
class ClipLibraryThumbnailPort(Protocol):
    def resolve_thumbnail_path(self, session: Any, clip_id: str) -> str | None:
        ...
