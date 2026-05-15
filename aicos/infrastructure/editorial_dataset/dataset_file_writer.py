"""Escritura de archivos de exportación."""

from __future__ import annotations

from pathlib import Path

from aicos.application.editorial_dataset.ports import DatasetFileWritePort


class LocalDatasetFileWriter(DatasetFileWritePort):
    def write_bytes(self, path: Path, data: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def write_text(self, path: Path, text: str, encoding: str = "utf-8") -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding=encoding)
