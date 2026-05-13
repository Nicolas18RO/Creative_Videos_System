"""Exploración paginada de la biblioteca de clips (Fase 2.5)."""

from __future__ import annotations

from typing import Any

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QGroupBox,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

DEFAULT_PAGE_SIZE = 50


class LibraryClipsPanel(QWidget):
    """Lista de clips con paginación; sin lógica de negocio (solo señales y presentación)."""

    clip_activated = pyqtSignal(dict)
    load_more_requested = pyqtSignal(int, int)

    def __init__(self, parent: QWidget | None = None, *, page_size: int = DEFAULT_PAGE_SIZE) -> None:
        super().__init__(parent)
        self._page_size = max(1, page_size)
        self._next_offset = 0
        self._total = 0
        self._loaded = 0

        box = QGroupBox("Explorar clips")
        lay = QVBoxLayout(self)
        lay.addWidget(box)
        inner = QVBoxLayout(box)
        self._status = QLabel("Cargando…")
        self._status.setWordWrap(True)
        inner.addWidget(self._status)
        self._list = QListWidget()
        self._list.itemClicked.connect(self._on_item_clicked)
        inner.addWidget(self._list, stretch=1)
        self._btn_more = QPushButton("Cargar más")
        self._btn_more.clicked.connect(self._on_load_more_click)
        self._btn_more.setEnabled(False)
        inner.addWidget(self._btn_more)

    def set_status_text(self, text: str) -> None:
        """Mensaje de estado (errores o avisos)."""
        self._status.setText(text)

    def reset(self) -> None:
        """Nueva sesión de listado (p. ej. al cambiar API base)."""
        self._list.clear()
        self._next_offset = 0
        self._total = 0
        self._loaded = 0
        self._status.setText("Listo para cargar.")
        self._btn_more.setEnabled(False)

    def apply_first_page(self, payload: dict[str, Any]) -> None:
        """Sustituye el contenido con la primera página de ``GET /library/clips``."""
        self._append_page_payload(payload, replace=True)

    def append_page(self, payload: dict[str, Any]) -> None:
        """Añade una página de resultados (paginación)."""
        self._append_page_payload(payload, replace=False)

    def _append_page_payload(self, payload: dict[str, Any], *, replace: bool) -> None:
        total = int(payload.get("total") or 0)
        offset = int(payload.get("offset") or 0)
        limit = int(payload.get("limit") or self._page_size)
        items = list(payload.get("items") or [])
        if replace:
            self._loaded = 0
            self._list.clear()
        self._total = total
        self._loaded = offset + len(items)
        self._next_offset = self._loaded

        for it in items:
            if not isinstance(it, dict):
                continue
            name = it.get("name") or it.get("filename") or it.get("clip_id") or "?"
            dur = it.get("duration_ms")
            dur_s = f"{int(dur) // 1000}s" if isinstance(dur, int) else "—"
            sid = it.get("scene_id")
            scene_part = f" · escena {str(sid)[:8]}…" if sid else ""
            label = f"{name} ({dur_s}){scene_part}"
            row = QListWidgetItem(label)
            row.setData(Qt.ItemDataRole.UserRole, it)
            row.setToolTip(it.get("relative_path") or "")
            self._list.addItem(row)

        self._status.setText(f"Mostrando {self._loaded} / {self._total} clips (pág. {limit}, offset {offset}).")
        self._btn_more.setEnabled(self._loaded < self._total)

    def _on_load_more_click(self) -> None:
        if self._loaded >= self._total:
            return
        self.load_more_requested.emit(self._next_offset, self._page_size)

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        self._emit_clip(item)

    def _emit_clip(self, item: QListWidgetItem) -> None:
        data = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(data, dict):
            self.clip_activated.emit(data)
