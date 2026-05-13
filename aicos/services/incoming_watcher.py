"""Watchdog sobre `incoming/`: clasificación M4 en segundo plano (PRD M4)."""

from __future__ import annotations

import asyncio
import fnmatch
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from aicos.config import get_config
from aicos.database.db import session_scope
from aicos.modules.clip_organizer import organize_clip

logger = logging.getLogger(__name__)

_VALID_VIDEO = {".mp4", ".mov", ".webm", ".avi", ".mkv"}
_executor: ThreadPoolExecutor | None = None
_observer: Observer | None = None


def _ignored_path(path: Path) -> bool:
    name = path.name
    if name.endswith(".aicos.json"):
        return True
    if "needs_review" in path.parts:
        return True
    for pat in get_config().library.ignore_patterns or []:
        if fnmatch.fnmatch(name, pat):
            return True
    return False


async def _process_incoming_file(path: Path) -> None:
    cfg = get_config()
    apply = bool(cfg.organizer.auto_classify)
    try:
        if apply:
            with session_scope() as session:
                res = await organize_clip(path, apply=True, session=session)
            logger.info("Incoming procesado (apply): %s -> %s", path, res.destination_path)
        else:
            res = await organize_clip(path, apply=False, session=None)
            if cfg.incoming_watcher.write_sidecar and path.is_file():
                sidecar = path.parent / f"{path.name}.aicos.json"
                sidecar.write_text(res.model_dump_json(indent=2), encoding="utf-8")
                logger.info("Incoming clasificado (sidecar): %s", sidecar)
    except Exception as e:
        logger.exception("Error procesando incoming %s: %s", path, e)


def _delayed_job(path_str: str) -> None:
    path = Path(path_str)
    time.sleep(get_config().incoming_watcher.settle_seconds)
    if not path.is_file():
        logger.debug("Archivo ya no existe (omitido): %s", path)
        return
    if _ignored_path(path):
        return
    if path.suffix.lower() not in _VALID_VIDEO:
        return
    asyncio.run(_process_incoming_file(path))


class _IncomingHandler(FileSystemEventHandler):
    def on_created(self, event) -> None:
        if event.is_directory:
            return
        p = Path(event.src_path)
        if _executor is None:
            return
        _executor.submit(_delayed_job, str(p))


def start_incoming_watcher() -> None:
    """Arranca el observador si `incoming_watcher.enabled` en config."""
    global _executor, _observer
    cfg = get_config()
    if not cfg.incoming_watcher.enabled:
        logger.info("Incoming watcher deshabilitado en config.")
        return
    if _observer is not None:
        logger.warning("Incoming watcher ya estaba iniciado.")
        return

    incoming = cfg.resolved_paths()["incoming_folder"]
    incoming.mkdir(parents=True, exist_ok=True)

    _executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="aicos_incoming")
    handler = _IncomingHandler()
    obs = Observer()
    obs.schedule(handler, str(incoming), recursive=True)
    obs.start()
    _observer = obs
    logger.info("Incoming watcher activo en %s", incoming)


def stop_incoming_watcher() -> None:
    """Detiene observador y pool (cierre de app)."""
    global _executor, _observer
    if _observer is not None:
        try:
            _observer.stop()
            _observer.join(timeout=10.0)
        except Exception as e:
            logger.warning("Al detener observer: %s", e)
        _observer = None
    if _executor is not None:
        try:
            _executor.shutdown(wait=False, cancel_futures=False)
        except Exception as e:
            logger.warning("Al cerrar executor: %s", e)
        _executor = None
    logger.info("Incoming watcher detenido.")
