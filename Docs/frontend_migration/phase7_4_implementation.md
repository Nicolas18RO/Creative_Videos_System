# Phase 7.4 — React Export Pipeline

## Objetivo

Convertir el Cinematic Studio en una plataforma **persistente y exportable**: serialización de proyectos, snapshots editoriales, manifests CapCut, upload de analyze desde React y restauración de sesión.

## Backend (Clean Architecture)

| Capa | Ruta |
|------|------|
| Dominio | `aicos/domain/export_pipeline/` — bundle, manifests, reglas |
| Aplicación | `aicos/application/export_pipeline/` — `ExportPipelineService`, `StudioAnalyzeUploadService` |
| Infraestructura | `aicos/infrastructure/export_pipeline/` — SQLite source, snapshots/manifests en disco |
| API | `aicos/api/routers/export_pipeline.py` — prefijo `/export` |
| Analyze upload | `POST /analyze/upload` — multipart en `analyze.py` |

### Endpoints export

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/export/projects/{id}/bundle` | Bundle editorial en vivo |
| GET | `/export/projects/{id}/manifest` | Manifest genérico de export |
| GET | `/export/projects/{id}/capcut-manifest` | Manifest orientado a CapCut |
| POST | `/export/projects/{id}/capcut-manifest/write` | Escribe JSON en `~/.aicos/exports/{id}/manifests/` |
| POST | `/export/projects/{id}/export-manifest/write` | Manifest genérico en disco |
| GET/POST | `/export/projects/{id}/snapshots` | Lista / persiste snapshot |
| GET | `/export/projects/{id}/snapshots/{sid}` | Carga snapshot |
| POST | `/export/projects/{id}/snapshots/{sid}/restore` | Restaura timeline en SQLite |

### Formato CapCut manifest (`aicos-capcut-manifest-v1`)

- Entradas ordenadas por escena con timecodes ms, paths absolutos de clip, texto guion
- `asset_dependencies` y `warnings` (clips faltantes, audio no en disco)
- Preparado para FO-2 (generador `.capcut`) y export XML futuro

### Snapshots

- Ruta: `~/.aicos/exports/{project_id}/snapshots/{snapshot_id}.json`
- Restauración vía `TimelineRestoreAdapter` → `SqlProjectTimelineRepository.replace_timeline`

## Frontend

```
features/cinematic-studio/export/
├── api/           exportPipelineApi, studioAnalyzeApi
├── presentation/  exportPresentation (resúmenes UI)
├── services/      studioSessionPersistence (localStorage)
├── hooks/         useExportPipeline, useStudioAnalyzeUpload
└── components/    ExportPipelinePanel, AnalyzeUploadPanel
```

- Proxy Vite: `/export`
- Restauración de sesión: proyecto + escena en `localStorage` tras bootstrap
- Estilos `.cs-exp-*`

## Verificación

```bash
python -m pytest tests/test_export_pipeline_rules.py -q
cd frontend && npm run build
```

## No modificado

- Editorial training, playback, timeline engine, PyQt legacy, pipelines M1–M3

## Siguiente (7.5+)

- FO-1 CapCut Export Watcher
- FO-2 generador `.capcut`
- Export Premiere / FCPXML
