import { useRef, useState } from "react";

import { useStudioAnalyzeUpload } from "../hooks/useStudioAnalyzeUpload";

type Props = {
  disabled?: boolean;
  onProjectCreated: (projectId: string) => void;
};

export function AnalyzeUploadPanel({ disabled, onProjectCreated }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [projectName, setProjectName] = useState("Nuevo proyecto");
  const { busy, error, progressLabel, analyzeFile } = useStudioAnalyzeUpload(onProjectCreated);

  const handlePick = () => inputRef.current?.click();

  const handleFile = (file: File | undefined) => {
    if (!file) return;
    void analyzeFile(file, projectName.trim() || "Proyecto");
  };

  return (
    <section className="cs-card cs-exp-analyze">
      <header className="cs-exp-analyze__head">
        <h2>Analizar guion (upload)</h2>
        <span className="cs-muted">POST /analyze/upload — Phase 7.4</span>
      </header>
      <div className="cs-exp-analyze__row">
        <label className="cs-exp-analyze__label">
          Nombre del proyecto
          <input
            type="text"
            className="cs-input"
            value={projectName}
            disabled={disabled || busy}
            onChange={(e) => setProjectName(e.target.value)}
          />
        </label>
        <button type="button" className="cs-btn" disabled={disabled || busy} onClick={handlePick}>
          Subir MP3/WAV
        </button>
        <input
          ref={inputRef}
          type="file"
          accept=".mp3,.wav,.m4a,.ogg,audio/*"
          className="cs-exp-analyze__file"
          onChange={(e) => handleFile(e.target.files?.[0])}
        />
      </div>
      {progressLabel && <p className="cs-muted">{progressLabel}</p>}
      {error && (
        <p className="cs-banner cs-banner--warn" role="alert">
          {error}
        </p>
      )}
    </section>
  );
}
