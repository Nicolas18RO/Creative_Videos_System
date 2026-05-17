import { memo } from "react";

import { formatTimelineTime } from "../../services/timelineTimeFormat";
import type { EditableScene } from "../../types/trainingWorkspace";
import { ClipTrimSlider } from "./ClipTrimSlider";
import { TimelineTimeInput } from "./TimelineTimeInput";

type Props = {
  scene: EditableScene;
  timelineDuration: number;
  disabled?: boolean;
  onTimingChange: (start: number, end: number) => void;
};

export const SceneTimingEditor = memo(function SceneTimingEditor({
  scene,
  timelineDuration,
  disabled,
  onTimingChange,
}: Props) {
  return (
    <div className="et-timing-editor">
      <ClipTrimSlider
        timeStart={scene.time_start}
        timeEnd={scene.time_end}
        timelineDuration={timelineDuration}
        disabled={disabled}
        onChange={onTimingChange}
      />
      <div className="et-row" style={{ marginTop: 8 }}>
        <TimelineTimeInput label="IN" value={scene.time_start} disabled={disabled} onChange={(v) => onTimingChange(v, scene.time_end)} />
        <TimelineTimeInput label="OUT" value={scene.time_end} disabled={disabled} onChange={(v) => onTimingChange(scene.time_start, v)} />
        <div className="et-stack">
          <span className="et-label">Duración</span>
          <span className="et-mono">{formatTimelineTime(scene.duration_seconds)}</span>
        </div>
      </div>
    </div>
  );
});
