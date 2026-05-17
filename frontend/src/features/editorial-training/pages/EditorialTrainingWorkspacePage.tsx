import "../components/editorial-training-workspace.css";

import { useCallback, useState } from "react";

import { commitTrainingSession } from "../api/editorialTrainingApi";
import { CommitTrainingPanel } from "../components/CommitTrainingPanel";
import { CreativeAnalysisLoader } from "../components/CreativeAnalysisLoader";
import { CreativeUploadZone } from "../components/CreativeUploadZone";
import { ReviewSummaryPanel } from "../components/ReviewSummaryPanel";
import { StyleSummaryPanel } from "../components/StyleSummaryPanel";
import { VisualTimelineEditor } from "../components/VisualTimelineEditor";
import { TrainingSessionForm } from "../components/TrainingSessionForm";
import { UploadProgressCard } from "../components/UploadProgressCard";
import { useCreativeUpload } from "../hooks/useCreativeUpload";
import { useTimelineAnalysis } from "../hooks/useTimelineAnalysis";
import { useTrainingSession } from "../hooks/useTrainingSession";
import { useTrainingWorkspaceStore } from "../state/trainingWorkspaceStore";
import type { TrainingStepId } from "../types/trainingWorkspace";

const STEPS: { id: TrainingStepId; label: string }[] = [
  { id: 1, label: "Sesión" },
  { id: 2, label: "Activos" },
  { id: 3, label: "Análisis IA" },
  { id: 4, label: "Timeline" },
  { id: 5, label: "Review Summary" },
  { id: 6, label: "Resumen" },
  { id: 7, label: "Commit" },
];

export function EditorialTrainingWorkspacePage() {
  const step = useTrainingWorkspaceStore((s) => s.step);
  const setStep = useTrainingWorkspaceStore((s) => s.setStep);
  const sessionId = useTrainingWorkspaceStore((s) => s.sessionId);
  const workspace = useTrainingWorkspaceStore((s) => s.workspace);
  const loading = useTrainingWorkspaceStore((s) => s.loading);
  const error = useTrainingWorkspaceStore((s) => s.error);
  const analysisStage = useTrainingWorkspaceStore((s) => s.analysisStage);
  const uploadVideoMeta = useTrainingWorkspaceStore((s) => s.uploadVideoMeta);
  const uploadAudioMeta = useTrainingWorkspaceStore((s) => s.uploadAudioMeta);
  const resetStore = useTrainingWorkspaceStore((s) => s.reset);

  const { createTraining, refresh } = useTrainingSession();
  const { uploadVideo, uploadAudio, videoProgress, audioProgress } = useCreativeUpload();
  const { runAnalysis } = useTimelineAnalysis();
  const [analysisBusy, setAnalysisBusy] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);

  const reload = useCallback(async (id: string) => refresh(id), [refresh]);

  const hasSession = Boolean(sessionId);
  const hasMedia =
    Boolean(workspace?.session.final_video_path) && Boolean(workspace?.session.audio_path);
  const canCommit = workspace?.session.status === "awaiting_human";

  return (
    <div className="et-root">
      <div className="et-shell">
        <header className="et-hero">
          <h1>Studio de entrenamiento editorial</h1>
          <p>
            Flujo guiado para subir creativos, analizar audio con AICOS, revisar el timeline visual y enviar refuerzo humano sin pegar
            JSON manualmente.
          </p>
        </header>

        <nav className="et-steps" aria-label="Pasos del flujo">
          {STEPS.map((s) => (
            <button
              key={s.id}
              type="button"
              className={`et-step-pill ${step === s.id ? "et-step-pill--active" : ""}`}
              onClick={() => setStep(s.id)}
            >
              {s.id}. {s.label}
            </button>
          ))}
          <button type="button" className="et-step-pill" onClick={() => resetStore()} style={{ marginLeft: "auto" }}>
            Reiniciar estado local
          </button>
        </nav>

        {error ? <div className="et-error">{error}</div> : null}
        {success ? <div className="et-success">{success}</div> : null}

        {step === 1 ? (
          <TrainingSessionForm
            disabled={loading}
            onCreate={async (body) => {
              setSuccess(null);
              const s = await createTraining(body);
              if (s) setStep(2);
            }}
          />
        ) : null}

        {step === 2 && hasSession ? (
          <>
            <div className="et-grid2">
              <CreativeUploadZone
                title="Vídeo creativo"
                subtitle="MP4, MOV o M4V. Se guarda en el volumen de entrenamiento del backend."
                accept=".mp4,.mov,.m4v"
                disabled={loading || !sessionId}
                onFile={(f) => sessionId && void uploadVideo(sessionId, f, reload)}
              />
              <CreativeUploadZone
                title="Audio guía"
                subtitle="WAV, MP3, M4A o FLAC. Debe corresponder al guion que AICOS transcribirá."
                accept=".wav,.mp3,.m4a,.flac"
                disabled={loading || !sessionId}
                onFile={(f) => sessionId && void uploadAudio(sessionId, f, reload)}
              />
            </div>
            <div className="et-grid2" style={{ marginTop: 4 }}>
              <UploadProgressCard
                label="Vídeo"
                filename={uploadVideoMeta?.filename}
                sizeBytes={uploadVideoMeta?.size_bytes}
                durationMs={uploadVideoMeta?.duration_ms}
                progress={videoProgress}
              />
              <UploadProgressCard
                label="Audio"
                filename={uploadAudioMeta?.filename}
                sizeBytes={uploadAudioMeta?.size_bytes}
                durationMs={uploadAudioMeta?.duration_ms}
                progress={audioProgress}
              />
            </div>
            <section className="et-card">
              <p className="et-muted" style={{ margin: 0 }}>
                Rutas en servidor: vídeo {workspace?.session.final_video_path || "—"} · audio {workspace?.session.audio_path || "—"}
              </p>
            </section>
          </>
        ) : null}

        {step === 3 && hasSession ? (
          <section className="et-card">
            <h2>Paso 3 — Análisis automático</h2>
            <p className="et-muted">
              Requiere vídeo y audio subidos. Orquesta transcripción, segmentación, ranking opcional y construcción del dataset editorial.
            </p>
            <div className="et-inline" style={{ marginTop: 12 }}>
              <button
                type="button"
                className="et-btn et-btn--primary"
                disabled={loading || analysisBusy || !hasMedia}
                onClick={() => {
                  if (!sessionId) return;
                  setSuccess(null);
                  setAnalysisBusy(true);
                  void runAnalysis(sessionId).finally(() => setAnalysisBusy(false));
                }}
              >
                Lanzar análisis AICOS
              </button>
              {!hasMedia ? <span className="et-muted">Sube ambos activos en el paso 2.</span> : null}
            </div>
            <CreativeAnalysisLoader active={analysisBusy} stageIndex={analysisStage} />
          </section>
        ) : null}

        {step === 4 ? (
          <>
            <section className="et-card">
              <p className="et-muted" style={{ margin: 0 }}>
                Estado de sesión: <strong>{workspace?.session.status ?? "—"}</strong> · Recorta IN/OUT y guarda con «Guardar ajustes del timeline».
              </p>
            </section>
            <VisualTimelineEditor creativeId={workspace?.session.creative_id ?? null} onReloadSession={reload} />
          </>
        ) : null}

        {step === 5 && hasSession ? (
          <ReviewSummaryPanel disabled={loading} onRefreshWorkspace={() => (sessionId ? reload(sessionId) : Promise.resolve())} />
        ) : null}

        {step === 6 ? <StyleSummaryPanel /> : null}

        {step === 7 && hasSession ? (
          <CommitTrainingPanel
            disabled={loading || !canCommit}
            onCommit={async () => {
              if (!sessionId) return;
              setSuccess(null);
              try {
                await commitTrainingSession(sessionId);
                await reload(sessionId);
                setSuccess("Aprendizaje consolidado. La sesión pasó a estado committed.");
              } catch (e) {
                useTrainingWorkspaceStore.getState().setError(e instanceof Error ? e.message : String(e));
              }
            }}
          />
        ) : null}

        {!hasSession && step !== 1 ? (
          <section className="et-card">
            <p className="et-muted">Crea primero una sesión en el paso 1.</p>
          </section>
        ) : null}
      </div>
    </div>
  );
}
