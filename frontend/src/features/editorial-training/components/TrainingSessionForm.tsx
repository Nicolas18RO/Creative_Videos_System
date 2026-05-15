import { useState } from "react";

import type { CreateTrainingSessionBody } from "../api/editorialTrainingApi";

type Props = {
  disabled?: boolean;
  onCreate: (body: CreateTrainingSessionBody) => Promise<void>;
};

export function TrainingSessionForm({ disabled, onCreate }: Props) {
  const [projectName, setProjectName] = useState("");
  const [creativeName, setCreativeName] = useState("");
  const [productCategory, setProductCategory] = useState("");
  const [notes, setNotes] = useState("");

  return (
    <section className="et-card">
      <h2>Paso 1 — Crear sesión de entrenamiento</h2>
      <div className="et-grid2">
        <div className="et-stack">
          <label className="et-label">Nombre del proyecto</label>
          <input
            className="et-input"
            value={projectName}
            onChange={(e) => setProjectName(e.target.value)}
            placeholder="Ej. Lanzamiento Q2"
            disabled={disabled}
          />
        </div>
        <div className="et-stack">
          <label className="et-label">Nombre del creativo</label>
          <input
            className="et-input"
            value={creativeName}
            onChange={(e) => setCreativeName(e.target.value)}
            placeholder="Ej. Spot salud 30s"
            disabled={disabled}
          />
        </div>
        <div className="et-stack">
          <label className="et-label">Producto / categoría</label>
          <input
            className="et-input"
            value={productCategory}
            onChange={(e) => setProductCategory(e.target.value)}
            placeholder="Ej. Bienestar / suplementos"
            disabled={disabled}
          />
        </div>
        <div className="et-stack">
          <label className="et-label">Notas</label>
          <textarea
            className="et-textarea"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Contexto editorial, mandatories, tono…"
            disabled={disabled}
          />
        </div>
      </div>
      <p className="et-muted" style={{ marginTop: 12 }}>
        AICOS generará un <code>creative_id</code> estable a partir del nombre del creativo si lo dejas en blanco en la API.
      </p>
      <div className="et-inline" style={{ marginTop: 16 }}>
        <button
          type="button"
          className="et-btn et-btn--primary"
          disabled={disabled || !creativeName.trim()}
          onClick={() =>
            void onCreate({
              project_name: projectName,
              creative_name: creativeName,
              product_category: productCategory,
              notes,
            })
          }
        >
          Crear sesión de entrenamiento
        </button>
      </div>
    </section>
  );
}
