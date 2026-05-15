"""Persistencia de activos de entrenamiento editorial (multipart → disco local)."""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from pathlib import Path

from aicos.application.editorial_dataset.ports import VideoMetadataProbePort, VideoProbeResult
from aicos.config import EditorialTrainingWorkspaceConfig

_SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]+")


@dataclass(frozen=True, slots=True)
class StoredEditorialUpload:
    """Metadatos mínimos tras guardar un archivo en el árbol de uploads."""

    absolute_path: str
    stored_filename: str
    size_bytes: int
    duration_ms: int | None


class EditorialTrainingUploadService:
    """Escribe vídeo/audio bajo ``uploads_root / session_id /`` con validación de política."""

    def __init__(
        self,
        *,
        workspace_cfg: EditorialTrainingWorkspaceConfig,
        uploads_root: Path,
        media_probe: VideoMetadataProbePort | None = None,
    ) -> None:
        self._cfg = workspace_cfg
        self._root = uploads_root
        self._probe = media_probe

    def _normalize_allowed(self, exts: list[str]) -> set[str]:
        return {e.lower() if e.startswith(".") else f".{e.lower()}" for e in exts}

    def _validate_size_and_ext(self, *, original_filename: str, data: bytes, allowed: set[str]) -> str:
        ext = Path(original_filename).suffix.lower()
        if ext not in allowed:
            raise ValueError("editorial_training_upload_extension_not_allowed")
        max_b = int(self._cfg.max_upload_mb) * 1024 * 1024
        if len(data) > max_b:
            raise ValueError("editorial_training_upload_too_large")
        return ext

    def _session_dir(self, session_id: str) -> Path:
        sid = (session_id or "").strip()
        if not sid or ".." in sid or "/" in sid or "\\" in sid:
            raise ValueError("editorial_training_invalid_session_id")
        if not re.fullmatch(r"[a-zA-Z0-9._-]{8,128}", sid):
            raise ValueError("editorial_training_invalid_session_id")
        d = (self._root / sid).resolve()
        root = self._root.resolve()
        try:
            d.relative_to(root)
        except ValueError as exc:
            raise ValueError("editorial_training_invalid_upload_path") from exc
        return d

    def _probe_duration(self, path: Path) -> int | None:
        if self._probe is None:
            return None
        try:
            res: VideoProbeResult = self._probe.probe_media(path)
            return int(res.duration_ms)
        except Exception:
            return None

    def save_video(self, session_id: str, original_filename: str, data: bytes) -> StoredEditorialUpload:
        ext = self._validate_size_and_ext(
            original_filename=original_filename, data=data, allowed=self._normalize_allowed(list(self._cfg.allowed_video_extensions))
        )
        d = self._session_dir(session_id)
        d.mkdir(parents=True, exist_ok=True)
        stem = _SAFE_NAME.sub("_", Path(original_filename).stem)[:80] or "video"
        stored = f"{stem}_{uuid.uuid4().hex[:10]}{ext}"
        path = d / stored
        path.write_bytes(data)
        dur = self._probe_duration(path)
        return StoredEditorialUpload(absolute_path=str(path), stored_filename=stored, size_bytes=len(data), duration_ms=dur)

    def save_audio(self, session_id: str, original_filename: str, data: bytes) -> StoredEditorialUpload:
        ext = self._validate_size_and_ext(
            original_filename=original_filename, data=data, allowed=self._normalize_allowed(list(self._cfg.allowed_audio_extensions))
        )
        d = self._session_dir(session_id)
        d.mkdir(parents=True, exist_ok=True)
        stem = _SAFE_NAME.sub("_", Path(original_filename).stem)[:80] or "audio"
        stored = f"{stem}_{uuid.uuid4().hex[:10]}{ext}"
        path = d / stored
        path.write_bytes(data)
        dur = self._probe_duration(path)
        return StoredEditorialUpload(absolute_path=str(path), stored_filename=stored, size_bytes=len(data), duration_ms=dur)
