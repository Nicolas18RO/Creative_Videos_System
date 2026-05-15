"""Loggers estructurados con prefijos fijos para trazabilidad editorial."""

from __future__ import annotations

import logging

_LOG = logging.getLogger("aicos.editorial_dataset")


def log_creative_timeline(msg: str, *args: object, **kwargs: object) -> None:
    _LOG.info("[CreativeTimeline] " + msg, *args, **kwargs)


def log_hook_detection(msg: str, *args: object, **kwargs: object) -> None:
    _LOG.info("[HookDetection] " + msg, *args, **kwargs)


def log_pattern_extraction(msg: str, *args: object, **kwargs: object) -> None:
    _LOG.info("[PatternExtraction] " + msg, *args, **kwargs)


def log_editorial_dataset(msg: str, *args: object, **kwargs: object) -> None:
    _LOG.info("[EditorialDataset] " + msg, *args, **kwargs)


def log_style_profile(msg: str, *args: object, **kwargs: object) -> None:
    _LOG.info("[StyleProfile] " + msg, *args, **kwargs)
