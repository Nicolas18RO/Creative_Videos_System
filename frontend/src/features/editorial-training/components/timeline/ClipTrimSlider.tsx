import { memo, useCallback } from "react";

import { roundSeconds } from "../../services/timelineTimeFormat";

type Props = {
  timeStart: number;
  timeEnd: number;
  timelineDuration: number;
  disabled?: boolean;
  onChange: (start: number, end: number) => void;
};

export const ClipTrimSlider = memo(function ClipTrimSlider({
  timeStart,
  timeEnd,
  timelineDuration,
  disabled,
  onChange,
}: Props) {
  const total = Math.max(timelineDuration, timeEnd, 1);
  const leftPct = (timeStart / total) * 100;
  const widthPct = ((timeEnd - timeStart) / total) * 100;

  const onInDrag = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const v = roundSeconds(Number(e.target.value));
      const nextStart = Math.min(v, timeEnd - 0.001);
      onChange(nextStart, timeEnd);
    },
    [onChange, timeEnd],
  );

  const onOutDrag = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const v = roundSeconds(Number(e.target.value));
      const nextEnd = Math.max(v, timeStart + 0.001);
      onChange(timeStart, nextEnd);
    },
    [onChange, timeStart],
  );

  return (
    <div className="et-trim-slider">
      <div className="et-trim-slider__rail">
        <div className="et-trim-slider__fill" style={{ left: `${leftPct}%`, width: `${widthPct}%` }} />
        <span className="et-trim-slider__in">IN</span>
        <span className="et-trim-slider__out">OUT</span>
      </div>
      <input
        type="range"
        className="et-trim-slider__handle et-trim-slider__handle--in"
        min={0}
        max={total}
        step={0.001}
        disabled={disabled}
        value={timeStart}
        onChange={onInDrag}
      />
      <input
        type="range"
        className="et-trim-slider__handle et-trim-slider__handle--out"
        min={0}
        max={total}
        step={0.001}
        disabled={disabled}
        value={timeEnd}
        onChange={onOutDrag}
      />
    </div>
  );
});
