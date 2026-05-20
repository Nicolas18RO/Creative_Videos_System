import { useMemo, useState } from "react";

import { mediaSrc } from "../api/timelineVisualizationApi";
import { sceneAudioContextText } from "../services/sceneAudioContext";
import { narrativeColor } from "../services/narrativeColors";
import type { EditableScene, TimelineVisualTrackDto } from "../types/trainingWorkspace";

type Props = {
  track: TimelineVisualTrackDto | null;
  scenes: EditableScene[];
  selectedIndex: number | null;
  zoom: number;
  onSelect: (sceneIndex: number) => void;
  onReorder: (fromIndex: number, toIndex: number) => void;
};

export function VisualTimelineTrack({ track, scenes, selectedIndex, zoom, onSelect, onReorder }: Props) {
  const [dragFrom, setDragFrom] = useState<number | null>(null);
  const total = track?.timeline_duration ?? Math.max(...scenes.map((s) => s.time_end), 1);

  const segments = useMemo(() => {
    return scenes.map((s) => {
      const widthPct = ((s.time_end - s.time_start) / total) * 100 * zoom;
      return { scene: s, widthPct: Math.max(4, widthPct) };
    });
  }, [scenes, total, zoom]);

  if (!scenes.length) {
    return <div className="vt-track vt-track--empty">Sin escenas en el timeline</div>;
  }

  return (
    <div className="vt-track">
      <div className="vt-track__scroll">
        <div className="vt-track__rail" style={{ width: `${Math.max(100, 100 * zoom)}%` }}>
          {segments.map(({ scene, widthPct }) => {
            const thumb = mediaSrc(scene.thumbnail_url);
            const color = narrativeColor(scene.narrative_intent || scene.narrative_role);
            const audioHint = sceneAudioContextText(scene);
            return (
              <button
                key={scene.scene_index}
                type="button"
                draggable
                className={`vt-seg ${selectedIndex === scene.scene_index ? "vt-seg--active" : ""} vt-seg--${scene.review_status || "pending"}`}
                style={{ flex: `0 0 ${widthPct}%`, borderColor: color }}
                title={audioHint ? `Audio: ${audioHint}` : `Escena ${scene.scene_index}`}
                aria-label={audioHint ? `Escena ${scene.scene_index}: ${audioHint}` : `Escena ${scene.scene_index}`}
                onClick={() => onSelect(scene.scene_index)}
                onDragStart={() => setDragFrom(scene.scene_index)}
                onDragOver={(e) => e.preventDefault()}
                onDrop={() => {
                  if (dragFrom !== null && dragFrom !== scene.scene_index) onReorder(dragFrom, scene.scene_index);
                  setDragFrom(null);
                }}
              >
                {thumb ? (
                  <img src={thumb} alt="" className="vt-seg__img" loading="lazy" draggable={false} />
                ) : (
                  <span className="vt-seg__ph">#{scene.scene_index}</span>
                )}
                <span className="vt-seg__label">{scene.narrative_role}</span>
                <span className="vt-seg__dur">{scene.duration_seconds.toFixed(1)}s</span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}

