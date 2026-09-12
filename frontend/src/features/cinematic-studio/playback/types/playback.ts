/** DTOs y tipos de motor de playback (Phase 7.3). */

export type PlaybackStateId =
  | "idle"
  | "loading"
  | "ready"
  | "playing"
  | "paused"
  | "seeking"
  | "scene_loop"
  | "error";

export type PlaybackMode = "timeline" | "scene";

export type PlaybackSceneMapDto = {
  scene_id: string;
  scene_index: number;
  start_sec: number;
  end_sec: number;
  duration_sec: number;
  text: string;
  concept: string;
  narrative_function: string;
  selected_clip_id?: string | null;
  clip_stream_url?: string | null;
};

export type PlaybackWaveformDto = {
  duration_sec: number;
  bucket_count: number;
  peaks: number[];
};

export type PlaybackSessionDto = {
  project_id: string;
  project_name: string;
  duration_sec: number;
  has_project_audio: boolean;
  has_waveform: boolean;
  audio_url: string;
  waveform_url: string;
  scenes: PlaybackSceneMapDto[];
  waveform: PlaybackWaveformDto | null;
};

export type PlaybackCueView = {
  sceneId: string;
  sceneIndex: number;
  text: string;
  startSec: number;
  endSec: number;
};

export type PlaybackEngineSnapshot = {
  state: PlaybackStateId;
  mode: PlaybackMode;
  currentTimeSec: number;
  durationSec: number;
  isPlaying: boolean;
  loopScene: boolean;
  activeSceneIndex: number | null;
  cue: PlaybackCueView | null;
  clipStreamUrl: string | null;
};
