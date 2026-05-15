"""Orquesta ingest, normalización, señales de estilo y patrones editoriales."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from aicos.application.editorial_dataset import logging_utils
from aicos.application.editorial_dataset.editorial_pattern_extraction_service import (
    EditorialPatternExtractionService,
)
from aicos.application.editorial_dataset.ports import (
    CreativeTimelinePersistenceWritePort,
    FilesystemPathPort,
    JsonTimelineReadPort,
    RawTimelineSceneInput,
    VideoMetadataProbePort,
)
from aicos.config import EditorialDatasetConfig
from aicos.domain.editorial_dataset.entities import CreativeTimeline, TimelineScene
from aicos.domain.editorial_dataset.rules import normalize_tag_list, validate_timeline_scenes
from aicos.domain.editorial_dataset.signals import build_style_profile_and_signals


class CreativeTimelineBuilderService:
    def __init__(
        self,
        *,
        cfg: EditorialDatasetConfig,
        fs: FilesystemPathPort,
        json_reader: JsonTimelineReadPort | None,
        video_probe: VideoMetadataProbePort | None,
        pattern_service: EditorialPatternExtractionService,
        persistence: CreativeTimelinePersistenceWritePort | None = None,
    ) -> None:
        self._cfg = cfg
        self._fs = fs
        self._json_reader = json_reader
        self._video_probe = video_probe
        self._patterns = pattern_service
        self._persistence = persistence

    def build_from_raw_scenes(
        self,
        *,
        creative_id: str,
        audio_path: str,
        final_video_path: str,
        raw_scenes: tuple[RawTimelineSceneInput, ...],
        session: Any | None = None,
    ) -> CreativeTimeline:
        if not self._cfg.enabled:
            raise RuntimeError("editorial_dataset_disabled")
        scenes = self._normalize_scenes(raw_scenes)
        ok, err = validate_timeline_scenes(scenes)
        if not ok:
            logging_utils.log_creative_timeline("validation_failed %s", err)
            raise ValueError(err)
        self._optional_path_checks(audio_path, final_video_path)

        profile, signals = build_style_profile_and_signals(
            scenes,
            hook_strength=0.0,
            cinematic_style_tags=(),
        )
        timeline = CreativeTimeline(
            creative_id=creative_id,
            audio_path=audio_path,
            final_video_path=final_video_path,
            timeline_scenes=scenes,
            style_profile=profile,
            style_signals=signals,
            editorial_patterns=(),
            hook_detection=(),
            created_at=datetime.now(timezone.utc),
            dataset_version=1,
        )
        timeline = self._patterns.attach_patterns_to_timeline(timeline, session=session)
        logging_utils.log_style_profile(
            "creative=%s pacing_score=%.3f hook_strength=%.3f",
            creative_id,
            timeline.style_signals.pacing_score,
            timeline.style_signals.hook_strength,
        )
        logging_utils.log_creative_timeline(
            "built creative=%s scenes=%s patterns=%s",
            creative_id,
            len(timeline.timeline_scenes),
            len(timeline.editorial_patterns),
        )
        if session is not None and self._persistence is not None:
            self._persistence.save(session, timeline)
            logging_utils.log_editorial_dataset("persisted creative=%s", creative_id)
            from aicos.services.editorial_style_embedding_factory import maybe_attach_style_embedding

            timeline = maybe_attach_style_embedding(session, timeline)
        return timeline

    def build_from_json_path(self, path: Path, session: Any | None = None) -> CreativeTimeline:
        if self._json_reader is None:
            raise RuntimeError("json_timeline_reader_not_configured")
        doc = self._json_reader.load_timeline_document(self._fs.resolve(path))
        creative_id = str(doc.get("creative_id") or path.stem)
        audio_path = str(doc.get("audio_path") or "")
        final_video_path = str(doc.get("final_video_path") or "")
        clips = doc.get("timeline") or doc.get("clips") or doc.get("scenes") or []
        raw: list[RawTimelineSceneInput] = []
        for item in clips:
            if not isinstance(item, dict):
                continue
            st = item.get("semantic_tags")
            if isinstance(st, str):
                sem = normalize_tag_list(st)
            elif isinstance(st, list):
                sem = normalize_tag_list(",".join(str(x) for x in st))
            else:
                sem = ()
            et = item.get("emotion_tags")
            if isinstance(et, str):
                emo = normalize_tag_list(et)
            elif isinstance(et, list):
                emo = normalize_tag_list(",".join(str(x) for x in et))
            else:
                emo = ()
            raw.append(
                RawTimelineSceneInput(
                    scene_index=int(item["scene_index"]),
                    clip_id=str(item.get("clip_id") or ""),
                    start_time=float(item.get("start_time", item.get("start", 0.0))),
                    end_time=float(item.get("end_time", item.get("end", 0.0))),
                    transition_type=str(item.get("transition_type") or "cut"),
                    narrative_role=str(item.get("narrative_role") or ""),
                    motion_intensity=float(item.get("motion_intensity", 0.0)),
                    visual_energy=float(item.get("visual_energy", 0.0)),
                    camera_type=str(item.get("camera_type") or ""),
                    semantic_tags=sem,
                    emotion_tags=emo,
                )
            )
        raw.sort(key=lambda r: r.scene_index)
        return self.build_from_raw_scenes(
            creative_id=creative_id,
            audio_path=audio_path,
            final_video_path=final_video_path,
            raw_scenes=tuple(raw),
            session=session,
        )

    def _normalize_scenes(self, raw: tuple[RawTimelineSceneInput, ...]) -> tuple[TimelineScene, ...]:
        out: list[TimelineScene] = []
        for r in raw:
            duration = max(0.0, r.end_time - r.start_time)
            out.append(
                TimelineScene(
                    scene_index=r.scene_index,
                    clip_id=r.clip_id,
                    start_time=r.start_time,
                    end_time=r.end_time,
                    duration=duration,
                    transition_type=r.transition_type,
                    narrative_role=r.narrative_role,
                    motion_intensity=max(0.0, min(1.0, r.motion_intensity)),
                    visual_energy=max(0.0, min(1.0, r.visual_energy)),
                    camera_type=r.camera_type,
                    semantic_tags=r.semantic_tags,
                    emotion_tags=r.emotion_tags,
                )
            )
        return tuple(out)

    def _optional_path_checks(self, audio_path: str, final_video_path: str) -> None:
        for label, p in (("audio", audio_path), ("video", final_video_path)):
            if not p:
                continue
            path = self._fs.resolve(Path(p))
            if not self._fs.exists(path):
                logging_utils.log_creative_timeline("missing_%s path=%s", label, path)
        if self._video_probe and final_video_path:
            vp = self._video_probe.probe_media(self._fs.resolve(Path(final_video_path)))
            logging_utils.log_creative_timeline(
                "ffprobe duration_ms=%s (reference_only)", vp.duration_ms
            )
