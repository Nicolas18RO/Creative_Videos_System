"""Tests aplicación timeline visual (puertos falsos)."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from aicos.application.timeline_visualization.timeline_visualization_service import TimelineVisualizationService
from aicos.config import TimelineVisualizationConfig
from aicos.domain.editorial_dataset.entities import CreativeTimeline, CreativeStyleProfile, EditorialStyleSignals, TimelineScene


class _FakeTimelineRead:
    def __init__(self, tl: CreativeTimeline) -> None:
        self._tl = tl

    def get_by_creative_id(self, session, creative_id: str):  # noqa: ARG002
        return self._tl if self._tl.creative_id == creative_id else None


class _FakePreviewRepo:
    def __init__(self) -> None:
        self.store: dict[str, tuple] = {}

    def list_by_creative_id(self, session, creative_id: str):  # noqa: ARG002
        return self.store.get(creative_id, ())

    def upsert_batch(self, session, creative_id: str, previews: tuple) -> None:  # noqa: ARG002
        self.store[creative_id] = previews

    def delete_by_creative_id(self, session, creative_id: str) -> None:  # noqa: ARG002
        self.store.pop(creative_id, None)


class _FakeMedia:
    def ensure_scene_thumbnail(self, **kwargs) -> Path | None:  # noqa: ARG003
        return Path(f"/tmp/thumb_{kwargs['scene_index']}.jpg")

    def ensure_scene_preview(self, **kwargs) -> Path | None:  # noqa: ARG003
        return Path(f"/tmp/prev_{kwargs['scene_index']}.mp4")

    def purge_creative_cache(self, creative_id: str) -> None:  # noqa: ARG002
        return None


class _NoClipThumb:
    def resolve_thumbnail_path(self, session, clip_id: str) -> str | None:  # noqa: ARG002
        return None


def _minimal_timeline(cid: str = "c1") -> CreativeTimeline:
    sp = CreativeStyleProfile(0.5, 0.5, 0.5, 0.2, 0.3, 0.4, ())
    ss = EditorialStyleSignals(0.5, 0.5, (), 0.4)
    scenes = (
        TimelineScene(0, "a", 0, 2, 2, "cut", "HOOK", 0.8, 0.9, "", (), ()),
        TimelineScene(1, "b", 2, 5, 3, "dissolve", "BENEFIT", 0.4, 0.5, "", (), ()),
    )
    return CreativeTimeline(
        creative_id=cid,
        audio_path="",
        final_video_path="",
        timeline_scenes=scenes,
        style_profile=sp,
        style_signals=ss,
        created_at=datetime.now(timezone.utc),
    )


def test_build_visual_track_curves_length() -> None:
    tl = _minimal_timeline()
    svc = TimelineVisualizationService(
        cfg=TimelineVisualizationConfig(enabled=True),
        timeline_read=_FakeTimelineRead(tl),
        preview_repo=_FakePreviewRepo(),
        media_gen=_FakeMedia(),
        clip_thumbs=_NoClipThumb(),
    )
    track = svc.build_visual_track(MagicMock(), "c1", previews=())
    assert track.timeline_duration == 5.0
    assert len(track.pacing_density) == 2
    assert len(track.motion_curve) == 2


def test_get_scene_inspection_not_found() -> None:
    tl = _minimal_timeline()
    svc = TimelineVisualizationService(
        cfg=TimelineVisualizationConfig(enabled=True),
        timeline_read=_FakeTimelineRead(tl),
        preview_repo=_FakePreviewRepo(),
        media_gen=_FakeMedia(),
        clip_thumbs=_NoClipThumb(),
    )
    with pytest.raises(ValueError, match="timeline_scene_not_found"):
        svc.get_scene_inspection(MagicMock(), "c1", 99)
