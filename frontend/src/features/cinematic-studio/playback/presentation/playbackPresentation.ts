import type {
  PlaybackCueView,
  PlaybackSceneMapDto,
  PlaybackSessionDto,
} from "../types/playback";

export function clampPlaybackTime(timeSec: number, durationSec: number): number {
  if (durationSec <= 0) return 0;
  return Math.max(0, Math.min(timeSec, durationSec));
}

export function activeSceneAtTime(
  scenes: PlaybackSceneMapDto[],
  timeSec: number,
): PlaybackSceneMapDto | null {
  const t = timeSec;
  for (const s of scenes) {
    if (t >= s.start_sec && t < s.end_sec - 1e-6) return s;
  }
  if (scenes.length && t >= scenes[scenes.length - 1].end_sec - 1e-6) {
    return scenes[scenes.length - 1];
  }
  return scenes[0] ?? null;
}

export function buildCueView(scene: PlaybackSceneMapDto | null): PlaybackCueView | null {
  if (!scene) return null;
  return {
    sceneId: scene.scene_id,
    sceneIndex: scene.scene_index,
    text: scene.text,
    startSec: scene.start_sec,
    endSec: scene.end_sec,
  };
}

export function sceneMarkers(scenes: PlaybackSceneMapDto[]): { index: number; atPct: number }[] {
  const dur = Math.max(...scenes.map((s) => s.end_sec), 0.001);
  return scenes.map((s) => ({
    index: s.scene_index,
    atPct: (s.start_sec / dur) * 100,
  }));
}

export function waveformBucketAtTime(
  peaks: number[],
  durationSec: number,
  timeSec: number,
): number {
  if (!peaks.length || durationSec <= 0) return 0;
  const idx = Math.min(
    peaks.length - 1,
    Math.max(0, Math.floor((timeSec / durationSec) * peaks.length)),
  );
  return peaks[idx] ?? 0;
}

export function sessionDurationSec(session: PlaybackSessionDto): number {
  const wf = session.waveform?.duration_sec ?? 0;
  return Math.max(session.duration_sec, wf);
}
