"""Aplicación FastAPI del AI-COS."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from aicos.api.routers import (
    analyze,
    benchmark,
    cinematic_intel,
    decisions,
    editorial_metadata,
    feedback,
    gaps,
    health,
    hooks,
    insights,
    library,
    organize,
    projects,
    search,
    taxonomy,
)
from aicos.database.db import init_db
from aicos.config import get_config
from aicos.services import analyze_health_service
from aicos.services.incoming_watcher import start_incoming_watcher, stop_incoming_watcher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    start_incoming_watcher()
    rt = get_config().runtime
    logger.info(
        "Runtime flags: local_only=%s offline_mode=%s use_openai=%s",
        rt.local_only,
        rt.offline_mode,
        rt.use_openai,
    )
    if rt.use_openai and (rt.local_only or rt.offline_mode):
        logger.warning(
            "use_openai=true pero local_only/offline_mode activo: el cliente OpenAI sigue deshabilitado "
            "hasta desactivar local_only y offline_mode."
        )
    analyze_health_service.log_startup_analyze_readiness()
    logger.info("AI-COS API iniciada (SQLite listo)")
    yield
    stop_incoming_watcher()


app = FastAPI(title="AI-COS", version="0.1.0", lifespan=lifespan)
app.include_router(health.router, tags=["health"])
app.include_router(search.router, prefix="/search", tags=["search"])
app.include_router(analyze.router, prefix="/analyze", tags=["analyze"])
app.include_router(gaps.router, prefix="/gaps", tags=["gaps"])
app.include_router(organize.router, prefix="/organize", tags=["organize"])
app.include_router(library.router, prefix="/library", tags=["library"])
app.include_router(insights.router, prefix="/insights", tags=["insights"])
app.include_router(decisions.router, prefix="/decisions", tags=["decisions"])
app.include_router(hooks.router, prefix="/hooks", tags=["hooks"])
app.include_router(benchmark.router, prefix="/benchmark", tags=["benchmark"])
app.include_router(cinematic_intel.router, prefix="/cinematic", tags=["cinematic"])
app.include_router(taxonomy.router, prefix="/taxonomy", tags=["taxonomy"])
app.include_router(feedback.router, prefix="/feedback", tags=["feedback"])
app.include_router(editorial_metadata.router, prefix="/editorial", tags=["editorial"])
app.include_router(projects.router, prefix="/projects", tags=["projects"])
