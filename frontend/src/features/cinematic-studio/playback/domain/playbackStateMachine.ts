import type { PlaybackStateId } from "../types/playback";

const ALLOWED: Record<PlaybackStateId, PlaybackStateId[]> = {
  idle: ["loading", "ready", "error"],
  loading: ["ready", "error", "idle"],
  ready: ["playing", "paused", "seeking", "scene_loop", "loading"],
  playing: ["paused", "seeking", "ready", "scene_loop", "error"],
  paused: ["playing", "seeking", "ready", "scene_loop", "error"],
  seeking: ["playing", "paused", "ready", "scene_loop"],
  scene_loop: ["playing", "paused", "ready", "seeking"],
  error: ["idle", "loading"],
};

export function canTransitionPlayback(current: PlaybackStateId, target: PlaybackStateId): boolean {
  if (current === target) return true;
  return (ALLOWED[current] ?? []).includes(target);
}

export function transitionPlayback(current: PlaybackStateId, target: PlaybackStateId): PlaybackStateId {
  if (!canTransitionPlayback(current, target)) return current;
  return target;
}
