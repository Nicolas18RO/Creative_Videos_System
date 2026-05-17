import { useRef, useState } from "react";

import { mediaSrc } from "../api/timelineVisualizationApi";
import type { EditableScene } from "../types/trainingWorkspace";

type Props = {
  scene: EditableScene | null;
};

export function ScenePreviewPlayer({ scene }: Props) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [hover, setHover] = useState(false);

  if (!scene) {
    return (
      <div className="vt-player vt-player--empty">
        <p>Selecciona una escena en la línea de tiempo</p>
      </div>
    );
  }

  const src = mediaSrc(scene.preview_video_url);

  return (
    <div className="vt-player">
      <div className="vt-player__meta">
        <strong>{scene.scene_type_label}</strong>
        <span>
          {scene.time_start.toFixed(2)}s – {scene.time_end.toFixed(2)}s · hook {(scene.hook_score * 100).toFixed(0)}%
        </span>
      </div>
      {src ? (
        <video
          ref={videoRef}
          className="vt-player__video"
          src={src}
          muted
          playsInline
          loop
          preload="metadata"
          onMouseEnter={() => {
            setHover(true);
            void videoRef.current?.play();
          }}
          onMouseLeave={() => {
            setHover(false);
            videoRef.current?.pause();
          }}
        />
      ) : (
        <div className="vt-player__placeholder">Generando preview…</div>
      )}
      <div className="vt-player__scrub">
        <input
          type="range"
          min={scene.time_start}
          max={scene.time_end}
          step={0.05}
          defaultValue={scene.time_start}
          onChange={(e) => {
            const v = Number(e.target.value);
            if (videoRef.current) videoRef.current.currentTime = Math.max(0, v - scene.time_start);
          }}
        />
        <span className="et-muted">{hover ? "Reproduciendo" : "Hover para preview"}</span>
      </div>
    </div>
  );
}
