# Phase 7.2 — React Timeline Engine (implementado)

## Backend (Clean Architecture)

| Capa | Ruta |
|------|------|
| Dominio | `aicos/domain/cinematic_timeline/` — merge, split, trim, reorder, validate |
| Aplicación | `aicos/application/cinematic_timeline/project_timeline_service.py` |
| Infra | `aicos/infrastructure/cinematic_timeline/sql_project_timeline_repository.py` |
| API | `aicos/api/routers/project_timeline.py` (montado en `/projects`) |

### Endpoints

| Método | Ruta | Acción |
|--------|------|--------|
| GET | `/projects/{id}/timeline` | Snapshot |
| POST | `/projects/{id}/timeline/reorder` | Drag reorder (`from_index`, `to_index`) |
| POST | `/projects/{id}/timeline/merge` | Fusionar escenas adyacentes |
| POST | `/projects/{id}/timeline/split` | Dividir por `split_at_ms` |
| POST | `/projects/{id}/timeline/trim` | Recortar IN/OUT (ms) |
| POST | `/projects/{id}/timeline/replace-clip` | Asignar `selected_clip_id` |

## Frontend

```
frontend/src/features/cinematic-studio/timeline/
├── api/projectTimelineApi.ts
├── presentation/timelineEnginePresentation.ts
├── services/timelineEngineHistory.ts
├── state/timelineEngineStore.ts      # separado de studioStore y training
├── hooks/useProjectTimelineEngine.ts # mutex + resync servidor
└── components/
    ├── ProjectTimelinePanel.tsx
    ├── StudioTimelineTrack.tsx       # drag reorder + previews
    ├── StudioTimelineToolbar.tsx
    └── StudioSceneMutationPanel.tsx  # trim / split / replace
```

Integrado en `CinematicRetrievalWorkspacePage` — sincroniza selección con retrieval (guion + candidatos).

## Garantías

- Sin lógica de ranking/retrieval en componentes UI
- Mutaciones autoritativas en servidor tras cada POST
- Mutex en cliente evita race conditions concurrentes
- Error → recarga snapshot desde GET
- Training editorial y PyQt no modificados

## Tests

`tests/test_cinematic_timeline_rules.py` — 5 passed

## Próximo (7.3)

- `POST /analyze` con upload desde React
- Export manifest CapCut
- Undo/redo con stack de snapshots servidor
