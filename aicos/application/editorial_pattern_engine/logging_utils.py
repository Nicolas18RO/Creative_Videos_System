"""Logging estructurado del motor de patrones editoriales (Fase 6.2)."""

from __future__ import annotations

import logging

_LOG = logging.getLogger("aicos.editorial_pattern_engine")


def log_pattern_engine(msg: str, *args: object, **kwargs: object) -> None:
    _LOG.info("[PatternEngine] " + msg, *args, **kwargs)
