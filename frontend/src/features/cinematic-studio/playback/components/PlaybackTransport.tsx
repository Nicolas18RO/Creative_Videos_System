type Props = {
  isPlaying: boolean;
  loopScene: boolean;
  currentTimeSec: number;
  durationSec: number;
  disabled?: boolean;
  onPlayPause: () => void;
  onToggleLoop: () => void;
  onSeek: (t: number) => void;
};

function fmt(sec: number): string {
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export function PlaybackTransport({
  isPlaying,
  loopScene,
  currentTimeSec,
  durationSec,
  disabled,
  onPlayPause,
  onToggleLoop,
  onSeek,
}: Props) {
  return (
    <div className="cs-pb-transport">
      <button type="button" className="cs-btn" disabled={disabled} onClick={onPlayPause}>
        {isPlaying ? "Pausa" : "Play"}
      </button>
      <button
        type="button"
        className={`cs-btn cs-btn--ghost${loopScene ? " cs-btn--active" : ""}`}
        disabled={disabled}
        onClick={onToggleLoop}
      >
        Loop escena
      </button>
      <span className="cs-pb-transport__time">
        {fmt(currentTimeSec)} / {fmt(durationSec)}
      </span>
      <input
        type="range"
        className="cs-pb-transport__scrub"
        min={0}
        max={durationSec || 1}
        step={0.05}
        value={currentTimeSec}
        disabled={disabled}
        onChange={(e) => onSeek(Number(e.target.value))}
      />
    </div>
  );
}
