"""Panel de decisiones del sistema (Fase 4): solo vía API, sin lógica de negocio."""

from __future__ import annotations

from typing import Any

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)


class DecisionPanel(QWidget):
    """Muestra puntuación, lista agrupada por severidad y un resumen de impacto."""

    reevaluate_requested = pyqtSignal(bool)

    def __init__(self) -> None:
        super().__init__()
        self._all_items: list[dict[str, Any]] = []

        root = QVBoxLayout(self)
        row = QHBoxLayout()
        row.addWidget(QLabel("Decisiones del sistema"))
        row.addStretch(1)
        self._btn = QPushButton("Re-evaluate System Decisions")
        self._btn.setToolTip("Recalcula en el servidor (insights + SQLite, sin re-embeddings).")
        self._btn.clicked.connect(lambda: self.reevaluate_requested.emit(True))
        row.addWidget(self._btn)
        root.addLayout(row)

        self._score = QLabel("Puntuación de decisiones: —")
        self._score.setStyleSheet("font-size: 15px; font-weight: bold;")
        root.addWidget(self._score)

        self._counts = QLabel("Totales: —")
        root.addWidget(self._counts)

        self._impact = QLabel("Impacto: —")
        self._impact.setWordWrap(True)
        root.addWidget(self._impact)

        filt = QHBoxLayout()
        filt.addWidget(QLabel("Tipo:"))
        self._type_combo = QComboBox()
        self._type_combo.addItems(["(todos)", "optimization", "content", "retrieval"])
        self._type_combo.currentTextChanged.connect(self._on_filter_changed)
        filt.addWidget(self._type_combo)
        filt.addWidget(QLabel("Severidad:"))
        self._sev_combo = QComboBox()
        self._sev_combo.addItems(["(todas)", "high", "medium", "low"])
        self._sev_combo.currentTextChanged.connect(self._on_filter_changed)
        filt.addStretch(1)
        root.addLayout(filt)

        self._tree = QTreeWidget()
        self._tree.setHeaderLabels(["Decisión", "Confianza"])
        self._tree.setColumnWidth(0, 520)
        root.addWidget(self._tree, stretch=1)

        self._status = QLabel("")
        self._status.setWordWrap(True)
        root.addWidget(self._status)

    def set_loading(self, loading: bool, message: str = "") -> None:
        self._btn.setEnabled(not loading)
        self._type_combo.setEnabled(not loading)
        self._sev_combo.setEnabled(not loading)
        self._status.setText(message or ("Cargando decisiones…" if loading else ""))

    def set_error(self, message: str) -> None:
        self.set_loading(False, "")
        self._status.setText(f"Error: {message}")

    def _on_filter_changed(self, _t: str) -> None:
        self._render_tree()

    def _filtered_items(self) -> list[dict[str, Any]]:
        t = self._type_combo.currentText()
        s = self._sev_combo.currentText()
        out = list(self._all_items)
        if t != "(todos)":
            out = [x for x in out if x.get("type") == t]
        if s != "(todas)":
            out = [x for x in out if x.get("severity") == s]
        return out

    def _render_tree(self) -> None:
        self._tree.clear()
        items = self._filtered_items()
        order = ("high", "medium", "low")
        labels = {"high": "Alta", "medium": "Media", "low": "Baja"}
        by_sev: dict[str, list[dict[str, Any]]] = {k: [] for k in order}
        for it in items:
            sev = str(it.get("severity") or "low")
            if sev in by_sev:
                by_sev[sev].append(it)
        for sev in order:
            group = by_sev[sev]
            if not group:
                continue
            top = QTreeWidgetItem([f"Severidad {labels[sev]} ({len(group)})", ""])
            top.setExpanded(True)
            self._tree.addTopLevelItem(top)
            for d in sorted(group, key=lambda x: (str(x.get("type")), str(x.get("id")))):
                title = f"[{d.get('type')}] {d.get('id')}"
                body = f"{d.get('explanation', '')}\n→ {d.get('suggested_action', '')}"
                conf = d.get("confidence_score")
                conf_s = f"{float(conf):.2f}" if isinstance(conf, (int, float)) else "—"
                child = QTreeWidgetItem([f"{title}\n{body}", conf_s])
                top.addChild(child)

    def apply_bundle(self, summary: dict[str, Any], lst: dict[str, Any], impact: dict[str, Any]) -> None:
        self.set_loading(False, "Listo.")
        score = summary.get("system_decision_score")
        if isinstance(score, (int, float)):
            self._score.setText(f"Puntuación de decisiones: {float(score):.1f} / 100")
        else:
            self._score.setText("Puntuación de decisiones: —")

        tot = summary.get("total_active_decisions")
        hi = summary.get("high_severity_count")
        dist = summary.get("decision_distribution") or {}
        dist_s = ", ".join(f"{k}={v}" for k, v in sorted(dist.items()))
        self._counts.setText(f"Activas: {tot} · Alta severidad: {hi} · Distribución: {dist_s or '—'}")

        areas = impact.get("most_affected_system_areas") or []
        cats = impact.get("categories_requiring_intervention") or []
        a_txt = "; ".join(f"{a.get('area')} ({a.get('decision_count')})" for a in areas[:5])
        c_txt = ", ".join(str(c.get("category")) for c in cats[:8])
        self._impact.setText(
            (f"Áreas afectadas: {a_txt or '—'}\nCategorías con intervención sugerida: {c_txt or '—'}")
        )

        self._all_items = list(lst.get("items") or [])
        self._render_tree()
