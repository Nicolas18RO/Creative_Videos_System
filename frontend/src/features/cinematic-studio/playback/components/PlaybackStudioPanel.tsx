import { useEffect, useMemo, useRef } from "react";

import { playbackMediaUrl } from "../api/playbackApi";
import { usePlaybackStudio } from "../hooks/usePlaybackStudio";
import { PlaybackMediaSurface } from "./PlaybackMediaSurface";
import { PlaybackSubtitles } from "./PlaybackSubtitles";
import { PlaybackTransport } from "./PlaybackTransport";
import { PlaybackWaveform } from "./PlaybackWaveform";

type Props = {
  projectId: string | null;
  sessionRefreshKey?: number;
  onSceneIndex?: (sceneIndex: number) => void;
};

export function PlaybackStudioPanel({ projectId, sessionRefreshKey, onSceneIndex }: Props) {
  const { session, error, snapshot, orchestrator, reload } = usePlaybackStudio(projectId, {
    onSceneIndex,
  });

  const reloadRef = useRef(reload);
  reloadRef.current = reload;

  useEffect(() => {
    if (sessionRefreshKey === undefined || sessionRefreshKey === 0) return;
    void reloadRef.current();
  }, [sessionRefreshKey]);

  const audioSrc = useMemo(
    () => (session?.audio_url ? playbackMediaUrl(session.audio_url) : ""),
    [session?.audio_url],
  );
  const clipSrc = useMemo(
    () => (snapshot.clipStreamUrl ? playbackMediaUrl(snapshot.clipStreamUrl) : null),
    [snapshot.clipStreamUrl],
  );

  if (!projectId) {
    return (
      <section className="cs-card cs-pb-panel">
        <p className="cs-muted">Selecciona un proyecto para abrir el Playback Studio.</p>
      </section>
    );
  }

  if (error) {
    return (
      <section className="cs-card cs-pb-panel">
        <p className="cs-banner cs-banner--warn">{error}</p>
      </section>
    );
  }

  if (!session) {
    return (
      <section className="cs-card cs-pb-panel">
        <p className="cs-muted">Cargando sesión de playback…</p>
      </section>
    );
  }

  const busy = snapshot.state === "loading";

  return (
    <section className="cs-card cs-pb-panel">
      <header className="cs-pb-panel__head">
        <h2>Playback Studio</h2>
        <span className="cs-muted">{session.project_name}</span>
      </header>

      <PlaybackMediaSurface
        session={session}
        audioSrc={audioSrc}
        clipSrc={clipSrc}
        isPlaying={snapshot.isPlaying}
        currentTimeSec={snapshot.currentTimeSec}
        onTimeUpdate={(t) => orchestrator.tickFromMedia(t)}
        onEnded={() => orchestrator.setPlaying(false)}
      />

      <PlaybackSubtitles cue={snapshot.cue} currentTimeSec={snapshot.currentTimeSec} />

      <PlaybackWaveform
        session={session}
        currentTimeSec={snapshot.currentTimeSec}
        disabled={busy}
        onSeek={(t) => orchestrator.seek(t, "waveform")}
      />

      <PlaybackTransport
        isPlaying={snapshot.isPlaying}
        loopScene={snapshot.loopScene}
        currentTimeSec={snapshot.currentTimeSec}
        durationSec={snapshot.durationSec}
        disabled={busy}
        onPlayPause={() => orchestrator.setPlaying(!snapshot.isPlaying)}
        onToggleLoop={() => orchestrator.toggleLoopScene()}
        onSeek={(t) => orchestrator.seek(t, "transport")}
      />
    </section>
  );
}
