import { useCallback, useState } from "react";

type Props = {
  title: string;
  subtitle: string;
  accept: string;
  disabled?: boolean;
  onFile: (file: File) => void;
};

export function CreativeUploadZone({ title, subtitle, accept, disabled, onFile }: Props) {
  const [active, setActive] = useState(false);

  const pick = useCallback(
    (list: FileList | null) => {
      if (!list?.length) return;
      onFile(list[0]);
    },
    [onFile],
  );

  return (
    <div className="et-card">
      <h2>{title}</h2>
      <p className="et-muted">{subtitle}</p>
      <div
        className={`et-drop ${active ? "et-drop--active" : ""}`}
        onDragOver={(e) => {
          e.preventDefault();
          setActive(true);
        }}
        onDragLeave={() => setActive(false)}
        onDrop={(e) => {
          e.preventDefault();
          setActive(false);
          pick(e.dataTransfer.files);
        }}
        style={{ marginTop: 14 }}
      >
        <p style={{ margin: "0 0 8px", color: "#e2e8f0" }}>Arrastra y suelta aquí</p>
        <p className="et-muted" style={{ margin: "0 0 12px" }}>
          Formatos: {accept}
        </p>
        <label className="et-btn et-btn--ghost" style={{ display: "inline-block", cursor: disabled ? "not-allowed" : "pointer" }}>
          Elegir archivo
          <input
            type="file"
            accept={accept}
            disabled={disabled}
            style={{ display: "none" }}
            onChange={(e) => pick(e.target.files)}
          />
        </label>
      </div>
    </div>
  );
}
