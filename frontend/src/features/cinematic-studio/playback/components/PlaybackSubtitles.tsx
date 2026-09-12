import type { PlaybackCueView } from "../types/playback";

type Props = {
  cue: PlaybackCueView | null;
  currentTimeSec: number;
};

export function PlaybackSubtitles({ cue, currentTimeSec }: Props) {
  if (!cue) {
    return (
      <div className="cs-pb-subs cs-pb-subs--empty">
        <span className="cs-muted">Sin subtítulo en esta posición</span>
      </div>
    );
  }
  return (
    <div className="cs-pb-subs" aria-live="polite">
      <span className="cs-pb-subs__meta">
        Escena #{cue.sceneIndex} · {currentTimeSec.toFixed(2)}s
      </span>
      <p className="cs-pb-subs__text">{cue.text || "—"}</p>
    </div>
  );
}
