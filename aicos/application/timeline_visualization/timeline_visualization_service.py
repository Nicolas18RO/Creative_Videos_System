"""Orquestación del timeline visual: previews, tracks e inspección."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from aicos.application.editorial_dataset.ports import CreativeTimelinePersistenceReadPort
from aicos.application.timeline_visualization.ports import (
    ClipLibraryThumbnailPort,
    TimelineClipPreviewPersistencePort,
    TimelineMediaGenerationPort,
)
from aicos.config import TimelineVisualizationConfig
from aicos.domain.editorial_dataset.entities import CreativeTimeline, TimelineScene
from aicos.domain.timeline_visualization.entities import (
    ClipVisualInspection,
    TimelineClipPreview,
    TimelineVisualTrack,
)
from aicos.domain.timeline_visualization.pacing import (
    build_motion_curve,
    build_pacing_density,
    build_transition_density,
    hook_probability_for_scene,
    scene_cut_speed,
    timeline_position_for_scene,
)

logger = logging.getLogger(__name__)


class TimelineVisualizationService:
    def __init__(
        self,
        *,
        cfg: TimelineVisualizationConfig,
        timeline_read: CreativeTimelinePersistenceReadPort,
        preview_repo: TimelineClipPreviewPersistencePort,
        media_gen: TimelineMediaGenerationPort,
        clip_thumbs: ClipLibraryThumbnailPort,
    ) -> None:
        self._cfg = cfg
        self._timeline_read = timeline_read
        self._preview_repo = preview_repo
        self._media_gen = media_gen
        self._clip_thumbs = clip_thumbs

    def _require_enabled(self) -> None:
        if not self._cfg.enabled:
            raise ValueError("timeline_visualization_disabled")

    def _load_timeline(self, session: Any, creative_id: str) -> CreativeTimeline:
        tl = self._timeline_read.get_by_creative_id(session, creative_id)
        if tl is None:
            raise ValueError("creative_timeline_not_found")
        return tl

    def _total_duration(self, timeline: CreativeTimeline) -> float:
        if not timeline.timeline_scenes:
            return 0.0
        return max(s.end_time for s in timeline.timeline_scenes)

    def _resolve_source_video(self, timeline: CreativeTimeline) -> Path | None:
        p = (timeline.final_video_path or "").strip()
        if not p:
            return None
        path = Path(p)
        return path if path.is_file() else None

    def _build_preview_for_scene(
        self,
        session: Any,
        *,
        timeline: CreativeTimeline,
        scene: TimelineScene,
        source: Path | None,
        total_dur: float,
    ) -> TimelineClipPreview:
        thumb_path = ""
        preview_path = ""
        lib_thumb = self._clip_thumbs.resolve_thumbnail_path(session, scene.clip_id)
        if lib_thumb and Path(lib_thumb).is_file():
            thumb_path = lib_thumb
        elif source is not None:
            t = self._media_gen.ensure_scene_thumbnail(
                source_video=source,
                creative_id=timeline.creative_id,
                scene_index=scene.scene_index,
                start_time=scene.start_time,
                end_time=scene.end_time,
            )
            if t is not None:
                thumb_path = str(t)
        if source is not None:
            pv = self._media_gen.ensure_scene_preview(
                source_video=source,
                creative_id=timeline.creative_id,
                scene_index=scene.scene_index,
                start_time=scene.start_time,
                end_time=scene.end_time,
            )
            if pv is not None:
                preview_path = str(pv)
        return TimelineClipPreview(
            clip_id=scene.clip_id,
            scene_index=scene.scene_index,
            thumbnail_path=thumb_path,
            preview_video_path=preview_path,
            start_time=scene.start_time,
            end_time=scene.end_time,
            duration=scene.duration,
            motion_score=scene.motion_intensity,
            narrative_role=scene.narrative_role,
            visual_cluster_id="",
            timeline_position=timeline_position_for_scene(scene, total_dur),
        )

    def generate_previews(self, session: Any, creative_id: str, *, force: bool = False) -> tuple[TimelineClipPreview, ...]:
        self._require_enabled()
        if force:
            self._media_gen.purge_creative_cache(creative_id)
            self._preview_repo.delete_by_creative_id(session, creative_id)
        timeline = self._load_timeline(session, creative_id)
        source = self._resolve_source_video(timeline)
        total = self._total_duration(timeline)
        previews = tuple(
            self._build_preview_for_scene(session, timeline=timeline, scene=s, source=source, total_dur=total)
            for s in timeline.timeline_scenes
        )
        self._preview_repo.upsert_batch(session, creative_id, previews)
        logger.info("[TimelineViz] generated %s previews creative=%s", len(previews), creative_id)
        return previews

    def rebuild(self, session: Any, creative_id: str) -> TimelineVisualTrack:
        self._require_enabled()
        previews = self.generate_previews(session, creative_id, force=True)
        return self.build_visual_track(session, creative_id, previews=previews)

    def build_visual_track(
        self,
        session: Any,
        creative_id: str,
        *,
        previews: tuple[TimelineClipPreview, ...] | None = None,
    ) -> TimelineVisualTrack:
        self._require_enabled()
        timeline = self._load_timeline(session, creative_id)
        if previews is None:
            previews = self._preview_repo.list_by_creative_id(session, creative_id)
            if not previews and timeline.timeline_scenes:
                previews = self.generate_previews(session, creative_id)
        scenes = timeline.timeline_scenes
        total = self._total_duration(timeline)
        return TimelineVisualTrack(
            creative_id=creative_id,
            timeline_duration=total,
            clip_previews=previews,
            pacing_density=build_pacing_density(scenes),
            transition_density=build_transition_density(scenes),
            motion_curve=build_motion_curve(scenes),
        )

    def get_scene_inspection(self, session: Any, creative_id: str, scene_index: int) -> ClipVisualInspection:
        self._require_enabled()
        timeline = self._load_timeline(session, creative_id)
        scene = next((s for s in timeline.timeline_scenes if s.scene_index == scene_index), None)
        if scene is None:
            raise ValueError("timeline_scene_not_found")
        return ClipVisualInspection(
            clip_id=scene.clip_id,
            scene_index=scene.scene_index,
            motion_intensity=scene.motion_intensity,
            visual_similarity=scene.visual_energy,
            cut_speed=scene_cut_speed(scene),
            transition_type=scene.transition_type,
            frame_density=min(1.0, 1.0 / max(scene.duration, 0.1)),
            hook_probability=hook_probability_for_scene(scene),
        )

    def resolve_media_path(
        self,
        session: Any,
        creative_id: str,
        scene_index: int,
        *,
        kind: str,
    ) -> Path | None:
        """Resuelve ruta en disco para thumbnail o preview (uso API)."""
        previews = self._preview_repo.list_by_creative_id(session, creative_id)
        if not previews:
            previews = self.generate_previews(session, creative_id)
        row = next((p for p in previews if p.scene_index == scene_index), None)
        if row is None:
            return None
        raw = row.thumbnail_path if kind == "thumbnail" else row.preview_video_path
        if not raw:
            return None
        path = Path(raw)
        return path if path.is_file() else None
