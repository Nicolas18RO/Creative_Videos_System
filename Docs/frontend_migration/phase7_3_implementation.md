# Phase 7.3 — React Playback Studio

## Objetivo

Migrar el playback cinematográfico del dashboard PyQt al frontend React (`features/cinematic-studio/playback/`), con sincronización timeline ↔ player, subtítulos, waveform, preview por clip y scrubbing — sin lógica editorial en componentes JSX.

## Backend (Clean Architecture)

| Capa | Ruta |
|------|------|
| Dominio | `aicos/domain/playback/` — estado, mapa de escenas, picos waveform, reglas temporales |
| Aplicación | `aicos/application/playback/` — `PlaybackSessionService`, presentación API |
| Infraestructura | `aicos/infrastructure/playback/` — resolución de media, extracción waveform (ffmpeg + caché) |
| API | `aicos/api/routers/playback.py` — prefijo `/playback` |

### Endpoints

- `GET /playback/projects/{project_id}/session` — sesión completa (escenas, URLs, waveform embebido)
- `GET /playback/projects/{project_id}/audio` — audio maestro del proyecto (FileResponse, Range)
- `GET /playback/clips/{clip_id}/stream` — preview de clip sin descarga completa
- `GET /playback/projects/{project_id}/waveform` — picos JSON (también incluidos en session)

## Frontend

```
frontend/src/features/cinematic-studio/playback/
├── api/playbackApi.ts
├── domain/playbackStateMachine.ts
├── presentation/playbackPresentation.ts
├── services/playbackOrchestrator.ts   # fuente de verdad temporal en cliente
├── state/playbackStore.ts
├── hooks/usePlaybackStudio.ts
└── components/
    ├── PlaybackStudioPanel.tsx
    ├── PlaybackMediaSurface.tsx
    ├── PlaybackSubtitles.tsx
    ├── PlaybackWaveform.tsx
    └── PlaybackTransport.tsx
```

### Principios

- **React no calcula escena activa ni cues** — solo `playbackPresentation.ts` y el orquestador.
- **Componentes emiten intenciones** (play, seek, loop) al `PlaybackOrchestrator`.
- **Sincronización bidireccional** con timeline/retrieval vía `onSceneIndex` y `orchestrator.selectScene()` desde la página.

### Integración

- `CinematicRetrievalWorkspacePage` — panel Playback Studio sobre el timeline engine.
- Proxy Vite: `/playback` → `http://127.0.0.1:8000`.
- Estilos: `.cs-pb-*` en `cinematic-studio.css`.

## Modos de reproducción

| Modo | Audio | Video | Subtítulos |
|------|-------|-------|------------|
| Timeline | MP3 del proyecto | clip de escena activa | `scene.text` |
| Loop escena | loop entre `start_sec`/`end_sec` | clip en loop | cue de escena |

## Verificación

```bash
python -m pytest tests/test_playback_rules.py tests/test_cinematic_timeline_rules.py -q
cd frontend && npm run build
```

## No modificado

- Editorial training (`features/editorial-training/`)
- Dashboard PyQt (`aicos/frontend/`)
- Pipelines de retrieval, feedback y ranking en backend

## Siguiente fase (7.4)

- `POST /analyze` con upload desde React
- Export CapCut desde el studio
