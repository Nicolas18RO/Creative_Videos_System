"""Presentación API playback."""

from __future__ import annotations

from aicos.application.playback.playback_session_service import PlaybackSessionBundle
from aicos.models.schemas import (
    PlaybackSceneMapOut,
    PlaybackSessionOut,
    PlaybackWaveformOut,
)


def session_to_out(bundle: PlaybackSessionBundle) -> PlaybackSessionOut:
    wf_out = None
    if bundle.waveform is not None:
        wf = bundle.waveform
        wf_out = PlaybackWaveformOut(
            duration_sec=wf.duration_sec,
            bucket_count=wf.bucket_count,
            peaks=list(wf.peaks),
        )
    return PlaybackSessionOut(
        project_id=bundle.project_id,
        project_name=bundle.project_name,
        duration_sec=bundle.duration_sec,
        has_project_audio=bundle.has_project_audio,
        has_waveform=bundle.has_waveform,
        audio_url=f"/playback/projects/{bundle.project_id}/audio",
        waveform_url=f"/playback/projects/{bundle.project_id}/waveform",
        scenes=[
            PlaybackSceneMapOut(
                scene_id=s.scene_id,
                scene_index=s.scene_index,
                start_sec=s.start_sec,
                end_sec=s.end_sec,
                duration_sec=s.duration_sec,
                text=s.text,
                concept=s.concept,
                narrative_function=s.narrative_function,
                selected_clip_id=s.selected_clip_id,
                clip_stream_url=(
                    f"/playback/clips/{s.selected_clip_id}/stream" if s.selected_clip_id else None
                ),
            )
            for s in bundle.scenes
        ],
        waveform=wf_out,
    )
