"""Factory playback Phase 7.3."""

from __future__ import annotations

from aicos.application.playback.playback_session_service import (
    PlaybackSessionService,
    PlaybackTimelineAdapter,
)
from aicos.infrastructure.playback.media_resolver import SqlPlaybackMediaResolver
from aicos.infrastructure.playback.waveform_extractor import extract_waveform_peaks


class _WaveformAdapter:
    def extract(self, audio_path, *, buckets: int = 320):
        return extract_waveform_peaks(audio_path, buckets=buckets)


def build_playback_session_service() -> PlaybackSessionService:
    return PlaybackSessionService(
        timeline=PlaybackTimelineAdapter(),
        media=SqlPlaybackMediaResolver(),
        waveform=_WaveformAdapter(),
    )
