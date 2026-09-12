# Phase 7.1 — Implementación (Cinematic Retrieval Workspace)

## Entregado

### Backend (mínimo, presentación)
- `GET /library/clips/{clip_id}/thumbnail` — sirve JPEG para UI web.
- `SceneDetailOut.selected_clip_id` — expone clip en timeline sin lógica en React.

### Frontend — arquitectura
```
frontend/src/
├── shared/api/client.ts
├── shared/media/thumbnailUrl.ts
└── features/cinematic-studio/
    ├── api/           # HTTP legacy (projects, search, feedback, library, gaps, health)
    ├── types/         # DTOs
    ├── presentation/  # View models (anti-corruption)
    ├── state/         # studioStore (Zustand, separado de training)
    ├── hooks/         # Orquestación únicamente
    ├── components/
    ├── pages/CinematicRetrievalWorkspacePage.tsx
    └── styles/cinematic-studio.css
```

### Paridad PyQt (7.1)
| Flujo | Estado |
|-------|--------|
| Listar proyectos / escenas | ✅ |
| Candidatos persistidos + preview `/search` | ✅ |
| Aceptar / rechazar (`POST /feedback`) | ✅ |
| Biblioteca paginada + búsqueda manual | ✅ |
| Explorar clip → similares | ✅ |
| Gaps M3 por escena | ✅ |
| Health banner (`GET /analyze/health`) | ✅ |
| `POST /analyze` / drop audio | 🔜 Phase 7.2 |

### Navegación
- App arranca en **Cinematic Studio**; enlace a **Entrenamiento editorial** (sin mezclar stores).

### Dev
```bash
uvicorn aicos.api.main:app --reload
cd frontend && npm run dev
```
Proxy Vite: `/analyze`, `/search`, `/feedback`, `/projects`, `/gaps`, `/library`.

### PyQt
Sin cambios. `aicos-dashboard` sigue operativo.
