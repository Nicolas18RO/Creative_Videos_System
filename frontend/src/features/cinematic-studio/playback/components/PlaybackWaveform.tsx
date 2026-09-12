import { useEffect, useRef } from "react";

import { sceneMarkers } from "../presentation/playbackPresentation";
import type { PlaybackSessionDto } from "../types/playback";

type Props = {
  session: PlaybackSessionDto;
  currentTimeSec: number;
  disabled?: boolean;
  onSeek: (timeSec: number) => void;
};

export function PlaybackWaveform({ session, currentTimeSec, disabled, onSeek }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const peaks = session.waveform?.peaks ?? [];
  const duration = session.waveform?.duration_sec ?? session.duration_sec;
  const markers = sceneMarkers(session.scenes);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);
    ctx.fillStyle = "#0f172a";
    ctx.fillRect(0, 0, w, h);
    if (!peaks.length) return;
    const mid = h / 2;
    const barW = w / peaks.length;
    ctx.fillStyle = "#475569";
    for (let i = 0; i < peaks.length; i++) {
      const amp = peaks[i] * (h * 0.42);
      ctx.fillRect(i * barW, mid - amp, Math.max(1, barW - 1), amp * 2);
    }
    ctx.strokeStyle = "rgba(56, 189, 248, 0.28)";
    for (const m of markers) {
      const x = (m.atPct / 100) * w;
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, h);
      ctx.stroke();
    }
    const headX = duration > 0 ? (currentTimeSec / duration) * w : 0;
    ctx.strokeStyle = "#38bdf8";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(headX, 0);
    ctx.lineTo(headX, h);
    ctx.stroke();
  }, [currentTimeSec, duration, markers, peaks]);

  const handleClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (disabled || duration <= 0) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    onSeek((x / rect.width) * duration);
  };

  return (
    <div className="cs-pb-wave">
      <canvas
        ref={canvasRef}
        className="cs-pb-wave__canvas"
        width={900}
        height={72}
        role="slider"
        aria-label="Waveform del guion"
        onClick={handleClick}
      />
      {!session.has_waveform && (
        <p className="cs-muted cs-pb-wave__hint">Sin waveform (ffmpeg requerido en el servidor).</p>
      )}
    </div>
  );
}
