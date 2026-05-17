import { useEffect, useState } from "react";

import { formatTimelineTime, parseTimelineTime, roundSeconds } from "../../services/timelineTimeFormat";

type Props = {
  label: string;
  value: number;
  disabled?: boolean;
  onChange: (seconds: number) => void;
};

export function TimelineTimeInput({ label, value, disabled, onChange }: Props) {
  const [text, setText] = useState(formatTimelineTime(value));

  useEffect(() => {
    setText(formatTimelineTime(value));
  }, [value]);

  return (
    <label className="et-stack et-time-input">
      <span className="et-label">{label}</span>
      <input
        className="et-input et-input--mono"
        disabled={disabled}
        value={text}
        onChange={(e) => setText(e.target.value)}
        onBlur={() => {
          const parsed = parseTimelineTime(text);
          if (parsed !== null) {
            onChange(roundSeconds(parsed));
            setText(formatTimelineTime(parsed));
          } else {
            setText(formatTimelineTime(value));
          }
        }}
        onKeyDown={(e) => {
          if (e.key === "Enter") (e.target as HTMLInputElement).blur();
        }}
      />
    </label>
  );
}
