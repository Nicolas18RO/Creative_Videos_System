"""Persistencia de proyectos y lectura de gaps."""

from __future__ import annotations

import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from aicos.database.db import Base
from aicos.models.schemas import (
    AnalyzedScene,
    AnalyzeAPIResponse,
    Gap,
    Scene,
    Transcript,
    TranscriptSegment,
)
from aicos.services import project_service


def test_persist_and_read_gaps() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(engine, expire_on_commit=False)
    session = Session()

    pid = str(uuid.uuid4())
    sid = str(uuid.uuid4())
    scene = Scene(
        scene_id=sid,
        scene_index=0,
        start_ms=0,
        end_ms=2000,
        duration_ms=2000,
        text="dolor de rodilla",
        concept="knee pain",
        narrative_function="PROBLEM",
    )
    gap = Gap(
        scene_id=sid,
        concept="knee pain",
        narrative_function="PROBLEM",
        gap_type="tiktok_search",
        tiktok_keywords=["knee pain tiktok", "rodilla dolor"],
    )
    analysis = AnalyzeAPIResponse(
        project_id=pid,
        project_name="Test",
        transcript=Transcript(
            full_text="dolor",
            language="es",
            segments=[TranscriptSegment(start_ms=0, end_ms=2000, text="dolor", words=[])],
            duration_ms=2000,
            audio_path="/tmp/x.mp3",
        ),
        total_duration_ms=2000,
        hook_count=0,
        scenes=[
            AnalyzedScene(
                scene=scene,
                recommendations=[],
                is_gap=True,
                gap=gap,
            )
        ],
    )

    project_service.persist_full_analysis(session, analysis, audio_path="/tmp/x.mp3")
    session.commit()

    out = project_service.get_project_gaps(session, pid)
    assert out.project_id == pid
    assert len(out.gaps) == 1
    assert out.gaps[0].scene_index == 0
    assert out.gaps[0].gap.tiktok_keywords[0] == "knee pain tiktok"


def test_persist_skips_gap_with_wrong_scene_id() -> None:
    """Un gap huérfano no debe abortar la persistencia completa."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(engine, expire_on_commit=False)
    session = Session()

    pid = str(uuid.uuid4())
    sid = str(uuid.uuid4())
    scene = Scene(
        scene_id=sid,
        scene_index=0,
        start_ms=0,
        end_ms=2000,
        duration_ms=2000,
        text="x",
        concept="c",
        narrative_function="PROBLEM",
    )
    bad_gap = Gap(
        scene_id=str(uuid.uuid4()),
        concept="orphan",
        narrative_function="PROBLEM",
        gap_type="tiktok_search",
        tiktok_keywords=["a"],
        taxonomy_suggestion="N/PROBLEM/GENERIC/",
    )
    analysis = AnalyzeAPIResponse(
        project_id=pid,
        project_name="Test2",
        transcript=Transcript(
            full_text="x",
            language="es",
            segments=[TranscriptSegment(start_ms=0, end_ms=2000, text="x", words=[])],
            duration_ms=2000,
            audio_path="/tmp/y.mp3",
        ),
        total_duration_ms=2000,
        hook_count=0,
        scenes=[
            AnalyzedScene(
                scene=scene,
                recommendations=[],
                is_gap=True,
                gap=bad_gap,
            )
        ],
    )
    project_service.persist_full_analysis(session, analysis, audio_path="/tmp/y.mp3")
    session.commit()
    out = project_service.get_project_gaps(session, pid)
    assert len(out.gaps) == 0
