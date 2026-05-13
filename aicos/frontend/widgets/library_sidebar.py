"""Barra lateral: estadísticas de biblioteca y búsqueda manual semántica (PRD Fase 2)."""

from __future__ import annotations

from typing import Any

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class LibrarySidebar(QWidget):
    """Stats + búsqueda libre contra ``POST /search``."""

    manual_search_requested = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        stats_box = QGroupBox("Biblioteca")
        sb_lay = QVBoxLayout(stats_box)
        self._stats_label = QLabel("Cargando…")
        self._stats_label.setWordWrap(True)
        self._stats_label.setTextFormat(Qt.TextFormat.RichText)
        sb_lay.addWidget(self._stats_label)
        root.addWidget(stats_box)

        search_box = QGroupBox("Búsqueda en biblioteca")
        se_lay = QVBoxLayout(search_box)
        row = QHBoxLayout()
        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("Ej: dolor de rodilla escaleras…")
        btn = QPushButton("Buscar")
        btn.clicked.connect(self._emit_search)
        row.addWidget(self._search_edit, stretch=1)
        row.addWidget(btn)
        se_lay.addLayout(row)
        self._results = QListWidget()
        self._results.setMaximumHeight(220)
        se_lay.addWidget(self._results)
        root.addWidget(search_box)
        root.addStretch(1)

    def set_stats(self, stats: dict[str, Any] | None, error: str | None = None) -> None:
        if error:
            self._stats_label.setText(f"Error stats: {error}")
            return
        if not stats:
            self._stats_label.setText("—")
            return
        total = stats.get("total_clips", "?")
        comp = stats.get("naming_compliant", "?")
        self._stats_label.setText(f"Clips indexados: <b>{total}</b><br>Con naming OK: <b>{comp}</b>")

    def set_manual_results(self, results: list[dict[str, Any]]) -> None:
        self._results.clear()
        for rec in results:
            path = rec.get("clip_path") or rec.get("clip_id") or ""
            score = rec.get("final_score", 0)
            short = (path[:70] + "…") if len(str(path)) > 70 else path
            it = QListWidgetItem(f"{float(score):.2f} — {short}")
            it.setToolTip(str(path))
            self._results.addItem(it)

    def _emit_search(self) -> None:
        q = self._search_edit.text().strip()
        if q:
            self.manual_search_requested.emit(q)
