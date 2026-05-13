"""Enumeraciones de pipeline multimodal (dominio puro)."""

from __future__ import annotations

from enum import Enum


class MultimodalBatchPhase(str, Enum):
    """Fases de alto nivel del batch OpenCLIP."""

    DISCOVER = "discover"
    KEYFRAMES = "keyframes"
    ENCODE = "encode"
    PERSIST = "persist"
    CHROMA = "chroma"
    DONE = "done"


class BatchItemStatus(str, Enum):
    """Estado por clip dentro del batch."""

    PENDING = "pending"
    SUCCESS = "success"
    SKIPPED = "skipped"
    FAILED = "failed"
