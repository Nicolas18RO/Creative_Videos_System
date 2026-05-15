"""Acceso local al filesystem (sin lógica editorial)."""

from __future__ import annotations

from pathlib import Path

from aicos.application.editorial_dataset.ports import FilesystemPathPort


class LocalFilesystemAdapter(FilesystemPathPort):
    def exists(self, path: Path) -> bool:
        return path.is_file() or path.is_dir()

    def resolve(self, path: Path) -> Path:
        return path.expanduser().resolve()
