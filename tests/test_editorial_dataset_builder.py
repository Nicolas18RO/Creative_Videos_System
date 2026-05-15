"""Tests del builder de timelines editoriales y persistencia."""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from aicos.application.editorial_dataset.creative_timeline_builder_service import CreativeTimelineBuilderService
from aicos.application.editorial_dataset.editorial_pattern_extraction_service import (
    EditorialPatternExtractionService,
)
from aicos.application.editorial_dataset.ports import RawTimelineSceneInput
from aicos.config import EditorialDatasetConfig, EditorialPatternEngineConfig
from aicos.database.db import Base
from aicos.domain.editorial_dataset.rules import validate_timeline_scenes
from aicos.infrastructure.editorial_dataset.filesystem_adapter import LocalFilesystemAdapter
from aicos.infrastructure.editorial_dataset.sqlite_creative_timeline_repository import (
    SqlCreativeTimelineRepository,
)


def _raw_sequence() -> tuple[RawTimelineSceneInput, ...]:
    roles = (
        ("mechanic_shot", "macro", ("motor", "taller"), ("tension",)),
        ("engine_macro", "macro", ("motor",), ("curiosity",)),
        ("smoke_plume", "wide", ("humo",), ("fear",)),
        ("driving_cinematic", "gimbal", ("carretera",), ("euphoria",)),
    ) * 2
    out: list[RawTimelineSceneInput] = []
    t = 0.0
    for i, (nr, cam, sem, emo) in enumerate(roles):
        dur = 0.85 if i < 4 else 0.9
        out.append(
            RawTimelineSceneInput(
                scene_index=i,
                clip_id=f"clip_{i}",
                start_time=t,
                end_time=t + dur,
                transition_type="whip" if i % 3 == 0 else "cut",
                narrative_role=nr,
                motion_intensity=0.75 if i < 4 else 0.55,
                visual_energy=0.8 if i < 2 else 0.5,
                camera_type=cam,
                semantic_tags=sem,
                emotion_tags=emo,
            )
        )
        t += dur
    return tuple(out)


def test_validate_timeline_scenes_ok() -> None:
    from aicos.domain.editorial_dataset.entities import TimelineScene

    scenes = tuple(
        TimelineScene(
            scene_index=i,
            clip_id=str(i),
            start_time=float(i),
            end_time=float(i) + 1.0,
            duration=1.0,
            transition_type="cut",
            narrative_role="hook",
            motion_intensity=0.5,
            visual_energy=0.5,
            camera_type="",
            semantic_tags=(),
            emotion_tags=(),
        )
        for i in range(3)
    )
    ok, err = validate_timeline_scenes(scenes)
    assert ok and err == ""


def test_builder_and_sqlite_roundtrip(tmp_path: Path) -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(engine, expire_on_commit=False)
    session = Session()

    cfg = EditorialDatasetConfig(enabled=True, detect_hooks=True, detect_patterns=True)
    patterns = EditorialPatternExtractionService(cfg, EditorialPatternEngineConfig())
    repo = SqlCreativeTimelineRepository()
    builder = CreativeTimelineBuilderService(
        cfg=cfg,
        fs=LocalFilesystemAdapter(),
        json_reader=None,
        video_probe=None,
        pattern_service=patterns,
        persistence=repo,
    )
    timeline = builder.build_from_raw_scenes(
        creative_id="creative_test_1",
        audio_path=str(tmp_path / "a.wav"),
        final_video_path=str(tmp_path / "v.mp4"),
        raw_scenes=_raw_sequence(),
        session=session,
    )
    session.commit()

    assert len(timeline.timeline_scenes) == 8
    assert timeline.style_signals.pacing_score > 0
    assert len(timeline.editorial_patterns) >= 1
    assert timeline.style_profile.motion_density > 0

    loaded = repo.get_by_creative_id(session, "creative_test_1")
    assert loaded is not None
    assert len(loaded.timeline_scenes) == 8
    assert abs(loaded.style_profile.hook_intensity - timeline.style_profile.hook_intensity) < 1e-6


def test_builder_disabled_raises() -> None:
    cfg = EditorialDatasetConfig(enabled=False)
    svc = EditorialPatternExtractionService(cfg, EditorialPatternEngineConfig())
    builder = CreativeTimelineBuilderService(
        cfg=cfg,
        fs=LocalFilesystemAdapter(),
        json_reader=None,
        video_probe=None,
        pattern_service=svc,
        persistence=None,
    )
    with pytest.raises(RuntimeError, match="editorial_dataset_disabled"):
        builder.build_from_raw_scenes(
            creative_id="x",
            audio_path="",
            final_video_path="",
            raw_scenes=_raw_sequence()[:2],
            session=None,
        )


def test_domain_has_no_sqlalchemy() -> None:
    import aicos.domain.editorial_dataset.entities as ent
    import aicos.domain.editorial_dataset.rules as rules
    import aicos.domain.editorial_dataset.signals as sig

    for mod in (ent, rules, sig):
        src = Path(mod.__file__).read_text(encoding="utf-8")
        assert "sqlalchemy" not in src.lower()
