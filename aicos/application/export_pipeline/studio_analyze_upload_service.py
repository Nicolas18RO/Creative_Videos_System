"""Upload de audio para analyze desde React (Phase 7.4)."""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from pathlib import Path


_SAFE = re.compile(r"[^A-Za-z0-9._-]+")
_ALLOWED = {".mp3", ".wav", ".m4a", ".ogg"}


@dataclass(frozen=True, slots=True)
class StoredStudioAudio:
    absolute_path: str
    stored_filename: str
    size_bytes: int


class StudioAnalyzeUploadService:
    def __init__(self, *, cache_root: Path, max_upload_mb: int = 256) -> None:
        self._root = cache_root.resolve()
        self._max_bytes = max_upload_mb * 1024 * 1024
        self._root.mkdir(parents=True, exist_ok=True)

    def save_audio(self, original_filename: str, data: bytes) -> StoredStudioAudio:
        ext = Path(original_filename).suffix.lower()
        if ext not in _ALLOWED:
            raise ValueError("studio_upload_extension_not_allowed")
        if len(data) > self._max_bytes:
            raise ValueError("studio_upload_too_large")
        if len(data) <= 0:
            raise ValueError("studio_upload_empty")
        stem = _SAFE.sub("_", Path(original_filename).stem)[:80] or "audio"
        stored = f"{stem}_{uuid.uuid4().hex[:12]}{ext}"
        path = self._root / stored
        path.write_bytes(data)
        return StoredStudioAudio(absolute_path=str(path), stored_filename=stored, size_bytes=len(data))
