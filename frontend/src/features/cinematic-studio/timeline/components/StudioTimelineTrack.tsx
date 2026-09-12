import { useMemo, useState } from "react";

import { libraryClipThumbnailUrl } from "../../../../shared/media/thumbnailUrl";
import { mapTimelineScenes } from "../presentation/timelineEnginePresentation";
import type { ProjectTimelineSceneDto } from "../types/timelineEngine";

type Props = {
  scenes: ProjectTimelineSceneDto[];
  timelineDurationSec: number;
  selectedSceneIndex: number | null;
  zoom: number;
  disabled?: boolean;
  onSelect: (sceneIndex: number) => void;
  onReorder: (fromIndex: number, toIndex: number) => void;
};

const NF_COLORS: Record<string, string> = {
  HOOK: "#f59e0b",
  PROBLEM: "#ef4444",
  BENEFIT: "#22c55e",
  PRODUCT: "#38bdf8",
  CTA: "#a78bfa",
};

export function StudioTimelineTrack({
  scenes,
  timelineDurationSec,
  selectedSceneIndex,
  zoom,
  disabled,
  onSelect,
  onReorder,
}: Props) {
  const [dragFrom, setDragFrom] = useState<number | null>(null);
  const views = useMemo(() => mapTimelineScenes(scenes), [scenes]);
  const total = Math.max(timelineDurationSec, 0.001);

  if (!views.length) {
    return <div className="cs-tl-track cs-tl-track--empty">Sin escenas en el timeline</div>;
  }

  return (
    <div className="cs-tl-track">
      <div className="cs-tl-track__scroll">
        <div className="cs-tl-track__rail" style={{ width: `${Math.max(100, 100 * zoom)}%` }}>
          {views.map((v) => {
            const widthPct = ((v.endSec - v.startSec) / total) * 100 * zoom;
            const color = NF_COLORS[v.narrativeFunction] ?? "#64748b";
            const thumb = v.selectedClipId ? libraryClipThumbnailUrl(v.selectedClipId) : null;
            return (
              <button
                key={v.sceneId}
                type="button"
                draggable={!disabled}
                className={`cs-tl-seg${selectedSceneIndex === v.sceneIndex ? " cs-tl-seg--active" : ""}${
                  v.selectedClipId ? " cs-tl-seg--has-clip" : ""
                }`}
                style={{ flex: `0 0 ${Math.max(5, widthPct)}%`, borderColor: color }}
                title={v.conceptPreview}
                onClick={() => onSelect(v.sceneIndex)}
                onDragStart={() => !disabled && setDragFrom(v.sceneIndex)}
                onDragOver={(e) => e.preventDefault()}
                onDrop={() => {
                  if (disabled || dragFrom === null || dragFrom === v.sceneIndex) return;
                  onReorder(dragFrom, v.sceneIndex);
                  setDragFrom(null);
                }}
              >
                {thumb ? (
                  <img src={thumb} alt="" className="cs-tl-seg__img" loading="lazy" draggable={false} />
                ) : (
                  <span className="cs-tl-seg__ph">#{v.sceneIndex}</span>
                )}
                <span className="cs-tl-seg__label">{v.narrativeFunction}</span>
                <span className="cs-tl-seg__dur">{v.durationSec.toFixed(1)}s</span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
