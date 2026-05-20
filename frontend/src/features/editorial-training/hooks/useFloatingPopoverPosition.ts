import { useLayoutEffect, useState } from "react";

export type PopoverRect = {
  top: number;
  left: number;
  width: number;
  maxHeight: number;
};

const DEFAULT_WIDTH = 400;
const VIEWPORT_MARGIN = 12;

export function useFloatingPopoverPosition(
  anchor: DOMRect | null,
  options?: { width?: number; estimatedHeight?: number },
): PopoverRect | null {
  const width = options?.width ?? DEFAULT_WIDTH;
  const estimatedHeight = options?.estimatedHeight ?? 440;
  const [rect, setRect] = useState<PopoverRect | null>(null);

  useLayoutEffect(() => {
    if (!anchor) {
      setRect(null);
      return;
    }
    const compute = () => {
      const vw = window.innerWidth;
      const vh = window.innerHeight;
      let left = anchor.left + anchor.width / 2 - width / 2;
      left = Math.max(VIEWPORT_MARGIN, Math.min(left, vw - width - VIEWPORT_MARGIN));

      let top = anchor.bottom + 8;
      const spaceBelow = vh - anchor.bottom - VIEWPORT_MARGIN;
      const spaceAbove = anchor.top - VIEWPORT_MARGIN;
      if (spaceBelow < estimatedHeight && spaceAbove > spaceBelow) {
        top = Math.max(VIEWPORT_MARGIN, anchor.top - Math.min(estimatedHeight, spaceAbove) - 8);
      }

      const maxHeight = Math.min(estimatedHeight, vh - top - VIEWPORT_MARGIN);
      setRect({ top, left, width, maxHeight: Math.max(200, maxHeight) });
    };
    compute();
    window.addEventListener("resize", compute);
    window.addEventListener("scroll", compute, true);
    return () => {
      window.removeEventListener("resize", compute);
      window.removeEventListener("scroll", compute, true);
    };
  }, [anchor, width, estimatedHeight]);

  return rect;
}
