import type { EditableScene } from "../types/trainingWorkspace";

const MAX_HISTORY = 80;

function cloneScenes(scenes: EditableScene[]): EditableScene[] {
  return scenes.map((s) => ({ ...s, semantic_tags: [...s.semantic_tags], emotion_tags: [...s.emotion_tags] }));
}

export function pushHistory(history: EditableScene[][], snapshot: EditableScene[]): EditableScene[][] {
  const next = [...history, cloneScenes(snapshot)];
  if (next.length > MAX_HISTORY) return next.slice(next.length - MAX_HISTORY);
  return next;
}

export function applyUndo(
  history: EditableScene[][],
  future: EditableScene[][],
  current: EditableScene[],
): { history: EditableScene[][]; future: EditableScene[][]; current: EditableScene[] } | null {
  if (!history.length) return null;
  const prev = history[history.length - 1];
  return {
    history: history.slice(0, -1),
    future: [cloneScenes(current), ...future],
    current: cloneScenes(prev),
  };
}

export function applyRedo(
  history: EditableScene[][],
  future: EditableScene[][],
  current: EditableScene[],
): { history: EditableScene[][]; future: EditableScene[][]; current: EditableScene[] } | null {
  if (!future.length) return null;
  const [next, ...rest] = future;
  return {
    history: pushHistory(history, current),
    future: rest,
    current: cloneScenes(next),
  };
}

export function scenesEqual(a: EditableScene[], b: EditableScene[]): boolean {
  if (a.length !== b.length) return false;
  return a.every((s, i) => {
    const t = b[i];
    return (
      s.scene_index === t.scene_index &&
      Math.abs(s.time_start - t.time_start) < 1e-3 &&
      Math.abs(s.time_end - t.time_end) < 1e-3
    );
  });
}
