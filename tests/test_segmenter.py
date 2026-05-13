"""Tests de segmentación y hooks."""

from __future__ import annotations

from aicos.core import segmenter
from aicos.models.schemas import Transcript, TranscriptSegment, TranscriptWord


def test_segmenter_basic_windowing() -> None:
    words = []
    t0 = 0
    for i in range(20):
        words.append(
            TranscriptWord(start_ms=t0 + i * 200, end_ms=t0 + (i + 1) * 200, word=f"w{i}")
        )
    tr = Transcript(
        full_text=" ".join(f"w{i}" for i in range(20)),
        language="es",
        segments=[
            TranscriptSegment(
                start_ms=0,
                end_ms=4000,
                text=" ".join(f"w{i}" for i in range(20)),
                words=words,
            )
        ],
        duration_ms=4000,
        audio_path="x.mp3",
    )
    scenes = segmenter.segment(tr)
    assert len(scenes) >= 1
    assert scenes[0].start_ms < scenes[0].end_ms


def test_hook_score_first_seconds() -> None:
    words = [
        TranscriptWord(start_ms=0, end_ms=400, word="Sientes"),
        TranscriptWord(start_ms=420, end_ms=800, word="dolor"),
        TranscriptWord(start_ms=820, end_ms=1200, word="secreto"),
        TranscriptWord(start_ms=1220, end_ms=1800, word="millones"),
        TranscriptWord(start_ms=1820, end_ms=2400, word="anos"),
    ]
    tr = Transcript(
        full_text="Sientes dolor secreto millones anos",
        language="es",
        segments=[TranscriptSegment(start_ms=0, end_ms=2400, text="Sientes dolor secreto millones anos", words=words)],
        duration_ms=8000,
        audio_path="x.mp3",
    )
    scenes = segmenter.segment(tr)
    assert any(s.hook_score > 0 for s in scenes)
