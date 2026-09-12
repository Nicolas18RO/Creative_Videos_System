/**
 * Orquestación de playback — única fuente de verdad temporal en el cliente.
 * Los componentes solo emiten intenciones; no calculan escena activa ni cues.
 */

import { transitionPlayback } from "../domain/playbackStateMachine";
import {
  activeSceneAtTime,
  buildCueView,
  clampPlaybackTime,
  sessionDurationSec,
} from "../presentation/playbackPresentation";
import type { PlaybackMode, PlaybackSessionDto, PlaybackStateId } from "../types/playback";

export type PlaybackStoreSlice = {
  session: PlaybackSessionDto | null;
  engineState: PlaybackStateId;
  mode: PlaybackMode;
  currentTimeSec: number;
  isPlaying: boolean;
  loopScene: boolean;
  activeSceneIndex: number | null;
  syncToken: number;
};

export type PlaybackPatch = Partial<PlaybackStoreSlice>;

export type SeekSource = "user" | "waveform" | "timeline" | "transport";

export class PlaybackOrchestrator {
  constructor(
    private readonly get: () => PlaybackStoreSlice,
    private readonly set: (patch: PlaybackPatch) => void,
    private readonly onSceneIndex?: (index: number) => void,
  ) {}

  loadSession(session: PlaybackSessionDto): void {
    const durationSec = sessionDurationSec(session);
    const scene = activeSceneAtTime(session.scenes, 0);
    this.set({
      session,
      engineState: transitionPlayback("loading", session.has_project_audio ? "ready" : "ready"),
      mode: "timeline",
      currentTimeSec: 0,
      isPlaying: false,
      loopScene: false,
      activeSceneIndex: scene?.scene_index ?? null,
      syncToken: this.get().syncToken + 1,
    });
    void durationSec;
  }

  reset(): void {
    this.set({
      session: null,
      engineState: "idle",
      mode: "timeline",
      currentTimeSec: 0,
      isPlaying: false,
      loopScene: false,
      activeSceneIndex: null,
    });
  }

  setLoading(): void {
    this.set({ engineState: transitionPlayback(this.get().engineState, "loading") });
  }

  setError(): void {
    this.set({ engineState: "error", isPlaying: false });
  }

  private applyTime(timeSec: number, source: SeekSource): void {
    const { session, loopScene, mode } = this.get();
    if (!session) return;
    const durationSec = sessionDurationSec(session);
    let t = clampPlaybackTime(timeSec, durationSec);
    const scene = activeSceneAtTime(session.scenes, t);

    if (loopScene && mode === "scene" && scene) {
      t = clampPlaybackTime(scene.start_sec, durationSec);
    }

    const nextState: PlaybackStateId =
      source === "user" || source === "waveform" || source === "timeline"
        ? transitionPlayback(this.get().engineState, "seeking")
        : this.get().engineState;

    this.set({
      currentTimeSec: t,
      activeSceneIndex: scene?.scene_index ?? null,
      engineState: nextState,
    });

    if (scene && (source === "waveform" || source === "timeline")) {
      this.onSceneIndex?.(scene.scene_index);
    }
  }

  seek(timeSec: number, source: SeekSource = "user"): void {
    this.applyTime(timeSec, source);
    const st = this.get().engineState;
    if (st === "seeking") {
      this.set({
        engineState: transitionPlayback(st, this.get().isPlaying ? "playing" : "paused"),
      });
    }
  }

  selectScene(sceneIndex: number, source: SeekSource = "timeline"): void {
    const { session } = this.get();
    if (!session) return;
    const scene = session.scenes.find((s) => s.scene_index === sceneIndex);
    if (!scene) return;
    this.applyTime(scene.start_sec, source);
    this.onSceneIndex?.(scene.scene_index);
  }

  tickFromMedia(timeSec: number): void {
    const { session, loopScene, mode, isPlaying } = this.get();
    if (!session || !isPlaying) return;
    const durationSec = sessionDurationSec(session);
    let t = clampPlaybackTime(timeSec, durationSec);
    const scene = activeSceneAtTime(session.scenes, t);

    if (loopScene && mode === "scene" && scene) {
      if (t >= scene.end_sec - 0.02) {
        t = scene.start_sec;
      }
    }

    const prevIdx = this.get().activeSceneIndex;
    this.set({
      currentTimeSec: t,
      activeSceneIndex: scene?.scene_index ?? null,
      engineState: transitionPlayback(this.get().engineState, "playing"),
    });
    if (scene && scene.scene_index !== prevIdx) {
      this.onSceneIndex?.(scene.scene_index);
    }
  }

  setPlaying(playing: boolean): void {
    const cur = this.get().engineState;
    this.set({
      isPlaying: playing,
      engineState: transitionPlayback(cur, playing ? "playing" : "paused"),
    });
  }

  toggleLoopScene(): void {
    this.set({ loopScene: !this.get().loopScene, mode: "scene" });
  }

  setMode(mode: PlaybackMode): void {
    this.set({ mode });
  }

  getSnapshot() {
    const s = this.get();
    const scene =
      s.session && s.activeSceneIndex !== null
        ? s.session.scenes.find((x) => x.scene_index === s.activeSceneIndex) ?? null
        : s.session
          ? activeSceneAtTime(s.session.scenes, s.currentTimeSec)
          : null;
    const clipUrl = scene?.clip_stream_url ?? null;
    return {
      state: s.engineState,
      mode: s.mode,
      currentTimeSec: s.currentTimeSec,
      durationSec: s.session ? sessionDurationSec(s.session) : 0,
      isPlaying: s.isPlaying,
      loopScene: s.loopScene,
      activeSceneIndex: s.activeSceneIndex,
      cue: buildCueView(scene),
      clipStreamUrl: clipUrl,
    };
  }
}
