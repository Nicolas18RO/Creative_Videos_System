import { mapSceneRailItem } from "../presentation/studioScenePresentation";
import type { ProjectDetailDto, ProjectGapsDto } from "../types/studio";

type Props = {
  projects: { id: string; name: string }[];
  selectedProjectId: string | null;
  detail: ProjectDetailDto | null;
  gaps: ProjectGapsDto | null;
  selectedSceneId: string | null;
  onSelectProject: (id: string) => void;
  onSelectScene: (sceneId: string) => void;
  onRefreshProjects: () => void;
};

export function ProjectSceneRail({
  projects,
  selectedProjectId,
  detail,
  gaps,
  selectedSceneId,
  onSelectProject,
  onSelectScene,
  onRefreshProjects,
}: Props) {
  const gapIds = new Set((gaps?.gaps ?? []).map((g) => g.gap.scene_id));

  return (
    <section className="cs-rail">
      <div className="cs-rail__col">
        <div className="cs-rail__head">
          <h2>Proyectos</h2>
          <button type="button" className="cs-btn cs-btn--ghost" onClick={onRefreshProjects}>
            Refrescar
          </button>
        </div>
        <ul className="cs-rail__list">
          {projects.map((p) => (
            <li key={p.id}>
              <button
                type="button"
                className={`cs-rail__item${selectedProjectId === p.id ? " cs-rail__item--active" : ""}`}
                onClick={() => onSelectProject(p.id)}
              >
                {p.name}
                <span className="cs-rail__id">{p.id.slice(0, 8)}…</span>
              </button>
            </li>
          ))}
        </ul>
      </div>
      <div className="cs-rail__col">
        <h2>Timeline · escenas</h2>
        {!detail && <p className="cs-muted">Selecciona un proyecto.</p>}
        <ul className="cs-rail__list cs-rail__list--scenes">
          {(detail?.scenes ?? []).map((sc) => {
            const item = mapSceneRailItem(sc, gapIds);
            return (
              <li key={sc.scene_id}>
                <button
                  type="button"
                  className={`cs-rail__item cs-rail__item--scene${
                    selectedSceneId === sc.scene_id ? " cs-rail__item--active" : ""
                  }${item.selectedClipId ? " cs-rail__item--has-clip" : ""}`}
                  onClick={() => onSelectScene(sc.scene_id)}
                >
                  <span className="cs-rail__scene-idx">#{item.sceneIndex}</span>
                  <span className="cs-rail__scene-nf">{item.narrativeFunction}</span>
                  <span className="cs-rail__scene-concept">{item.conceptPreview}</span>
                  {item.isHook && <span className="cs-rail__tag">HOOK</span>}
                  {item.hasGap && <span className="cs-rail__tag cs-rail__tag--gap">GAP</span>}
                </button>
              </li>
            );
          })}
        </ul>
      </div>
    </section>
  );
}
