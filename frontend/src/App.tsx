import { useState } from "react";

import { CinematicRetrievalWorkspacePage } from "./features/cinematic-studio/pages/CinematicRetrievalWorkspacePage";
import { EditorialTrainingWorkspacePage } from "./features/editorial-training/pages/EditorialTrainingWorkspacePage";

export type AppSurface = "studio" | "training";

export function App() {
  const [surface, setSurface] = useState<AppSurface>("studio");

  if (surface === "training") {
    return (
      <div className="app-shell">
        <nav className="app-nav">
          <button type="button" className="app-nav__btn" onClick={() => setSurface("studio")}>
            ← Cinematic Studio
          </button>
        </nav>
        <EditorialTrainingWorkspacePage />
      </div>
    );
  }

  return (
    <CinematicRetrievalWorkspacePage onOpenTraining={() => setSurface("training")} />
  );
}
