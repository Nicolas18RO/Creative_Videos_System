import { useEffect, useRef } from "react";

import type { PlaybackSessionDto } from "../types/playback";

type Props = {
  session: PlaybackSessionDto;
  audioSrc: string;
  clipSrc: string | null;
  isPlaying: boolean;
  currentTimeSec: number;
  onTimeUpdate: (t: number) => void;
  onEnded: () => void;
};

export function PlaybackMediaSurface({
  session,
  audioSrc,
  clipSrc,
  isPlaying,
  currentTimeSec,
  onTimeUpdate,
  onEnded,
}: Props) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const lastSeek = useRef(-1);

  useEffect(() => {
    const a = audioRef.current;
    if (!a) return;
    if (Math.abs(a.currentTime - currentTimeSec) > 0.35 && lastSeek.current !== currentTimeSec) {
      a.currentTime = currentTimeSec;
      lastSeek.current = currentTimeSec;
    }
  }, [currentTimeSec]);

  useEffect(() => {
    const a = audioRef.current;
    if (!a) return;
    if (isPlaying) {
      void a.play().catch(() => undefined);
    } else {
      a.pause();
    }
  }, [isPlaying]);

  useEffect(() => {
    const v = videoRef.current;
    if (!v || !clipSrc) return;
    if (isPlaying) {
      void v.play().catch(() => undefined);
    } else {
      v.pause();
    }
  }, [isPlaying, clipSrc]);

  return (
    <div className="cs-pb-media">
      {session.has_project_audio ? (
        <audio
          ref={audioRef}
          className="cs-pb-media__audio"
          src={audioSrc}
          preload="metadata"
          onTimeUpdate={() => {
            const t = audioRef.current?.currentTime ?? 0;
            onTimeUpdate(t);
          }}
          onEnded={onEnded}
        />
      ) : (
        <p className="cs-muted">Audio del proyecto no disponible en disco.</p>
      )}
      {clipSrc ? (
        <video
          key={clipSrc}
          ref={videoRef}
          className="cs-pb-media__video"
          src={clipSrc}
          muted
          playsInline
          preload="metadata"
          loop
        />
      ) : (
        <div className="cs-pb-media__video-ph">Sin clip seleccionado para la escena</div>
      )}
    </div>
  );
}
