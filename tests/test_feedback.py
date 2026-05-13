"""Feedback sobre recomendaciones."""

import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from aicos.database.db import Base, RecommendationRow, SceneRow
from aicos.services import project_service


def test_update_recommendation_feedback() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(engine, expire_on_commit=False)
    s = Session()

    pid = str(uuid.uuid4())
    sid = str(uuid.uuid4())
    rid = str(uuid.uuid4())

    from aicos.database.db import ProjectRow

    s.add(
        ProjectRow(
            id=pid,
            name="P",
            status="draft",
        )
    )
    s.add(
        SceneRow(
            id=sid,
            project_id=pid,
            scene_index=0,
            start_ms=0,
            end_ms=1000,
            duration_ms=1000,
            text="t",
            concept="c",
            narrative_function="HOOK",
        )
    )
    s.add(
        RecommendationRow(
            id=rid,
            scene_id=sid,
            clip_id="clip-1",
            similarity_score=0.8,
            taxonomy_boost=0.1,
            final_score=0.9,
            rank=1,
            accepted=None,
        )
    )
    s.commit()

    n = project_service.update_recommendation_feedback(
        s, scene_id=sid, clip_id="clip-1", accepted=True, rank=1
    )
    s.commit()
    assert n == 1
    sc = s.get(SceneRow, sid)
    assert sc is not None
    assert sc.selected_clip_id == "clip-1"
    rec = s.get(RecommendationRow, rid)
    assert rec is not None
    assert rec.accepted is True
