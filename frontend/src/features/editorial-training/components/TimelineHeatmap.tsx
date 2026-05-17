import type { TimelineVisualTrackDto } from "../types/trainingWorkspace";
import { narrativeColor } from "../services/narrativeColors";

type Props = {
  track: TimelineVisualTrackDto | null;
  selectedIndex: number | null;
  onSelect: (sceneIndex: number) => void;
};

export function TimelineHeatmap({ track, selectedIndex, onSelect }: Props) {
  if (!track || !track.clip_previews.length) {
    return <div className="vt-heatmap vt-heatmap--empty">Sin datos de pacing visual</div>;
  }

  return (
    <div className="vt-heatmap">
      <div className="vt-heatmap__row">
        <span className="vt-heatmap__label">Motion</span>
        <div className="vt-heatmap__cells">
          {track.motion_curve.map((v, i) => (
            <button
              key={`m-${i}`}
              type="button"
              className={`vt-heatcell ${selectedIndex === track.clip_previews[i]?.scene_index ? "vt-heatcell--on" : ""}`}
              style={{
                opacity: 0.25 + v * 0.75,
                background: narrativeColor(track.clip_previews[i]?.narrative_role ?? ""),
              }}
              title={`Escena ${i} motion ${(v * 100).toFixed(0)}%`}
              onClick={() => onSelect(track.clip_previews[i].scene_index)}
            />
          ))}
        </div>
      </div>
      <div className="vt-heatmap__row">
        <span className="vt-heatmap__label">Pacing</span>
        <div className="vt-heatmap__cells">
          {track.pacing_density.map((v, i) => (
            <button
              key={`p-${i}`}
              type="button"
              className={`vt-heatcell vt-heatcell--pacing ${selectedIndex === track.clip_previews[i]?.scene_index ? "vt-heatcell--on" : ""}`}
              style={{ height: `${20 + v * 48}px` }}
              title={`Pacing ${(v * 100).toFixed(0)}%`}
              onClick={() => onSelect(track.clip_previews[i].scene_index)}
            />
          ))}
        </div>
      </div>
      <div className="vt-heatmap__row">
        <span className="vt-heatmap__label">Hooks</span>
        <div className="vt-heatmap__cells">
          {track.clip_previews.map((p) => (
            <button
              key={`h-${p.scene_index}`}
              type="button"
              className={`vt-heatcell vt-heatcell--hook ${selectedIndex === p.scene_index ? "vt-heatcell--on" : ""}`}
              style={{ opacity: p.narrative_role.toUpperCase() === "HOOK" ? 1 : 0.25 }}
              onClick={() => onSelect(p.scene_index)}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
