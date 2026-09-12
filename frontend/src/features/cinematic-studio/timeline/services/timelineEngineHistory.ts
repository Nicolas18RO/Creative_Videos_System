import type { ProjectTimelineSceneDto } from "../types/timelineEngine";

const MAX = 60;

function clone(scenes: ProjectTimelineSceneDto[]): ProjectTimelineSceneDto[] {
  return scenes.map((s) => ({ ...s }));
}

export function pushTimelineHistory(
  history: ProjectTimelineSceneDto[][],
  snapshot: ProjectTimelineSceneDto[],
): ProjectTimelineSceneDto[][] {
  const next = [...history, clone(snapshot)];
  return next.length > MAX ? next.slice(next.length - MAX) : next;
}

export function timelineUndo(
  history: ProjectTimelineSceneDto[][],
  future: ProjectTimelineSceneDto[][],
  current: ProjectTimelineSceneDto[],
): { history: ProjectTimelineSceneDto[][]; future: ProjectTimelineSceneDto[][]; current: ProjectTimelineSceneDto[] } | null {
  if (!history.length) return null;
  const prev = history[history.length - 1];
  return {
    history: history.slice(0, -1),
    future: [clone(current), ...future],
    current: clone(prev),
  };
}

export function timelineRedo(
  history: ProjectTimelineSceneDto[][],
  future: ProjectTimelineSceneDto[][],
  current: ProjectTimelineSceneDto[],
): { history: ProjectTimelineSceneDto[][]; future: ProjectTimelineSceneDto[][]; current: ProjectTimelineSceneDto[] } | null {
  if (!future.length) return null;
  const [next, ...rest] = future;
  return {
    history: pushTimelineHistory(history, current),
    future: rest,
    current: clone(next),
  };
}
