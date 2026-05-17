"""Puerto de aplicación para previews (delega en timeline_visualization / FFmpeg infra)."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable


@runtime_checkable
class EditorialReviewThumbnailPort(Protocol):
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
