"""Panel de insights del sistema (Fase 3): datos vía API, carga en hilo aparte."""

from __future__ import annotations

import json
from typing import Any

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class InsightsPanel(QWidget):
    """Muestra salud, gaps agregados y tendencias; emite petición de recarga."""

    recompute_requested = pyqtSignal(bool)

    def __init__(self) -> None:
        super().__init__()
        root = QVBoxLayout(self)

        row = QHBoxLayout()
        row.addWidget(QLabel("Insights del sistema"))
        row.addStretch(1)
        self._btn_refresh = QPushButton("Recompute Insights")
        self._btn_refresh.setToolTip("Invalida caché del servidor y vuelve a pedir resúmenes (sin recomputar embeddings).")
        self._btn_refresh.clicked.connect(lambda: self.recompute_requested.emit(True))
        row.addWidget(self._btn_refresh)
        root.addLayout(row)

        self._health = QLabel("Salud: —")
        self._health.setStyleSheet("font-size: 16px; font-weight: bold;")
        root.addWidget(self._health)

        self._coverage = QLabel("Cobertura: —")
        root.addWidget(self._coverage)

        self._embed = QLabel("Embeddings / Chroma: —")
        root.addWidget(self._embed)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        inner = QWidget()
        inner_l = QVBoxLayout(inner)

        inner_l.addWidget(QLabel("Gaps y zonas débiles (agregado)"))
        self._gaps_view = QPlainTextEdit()
        self._gaps_view.setReadOnly(True)
        self._gaps_view.setMinimumHeight(140)
        inner_l.addWidget(self._gaps_view)

        inner_l.addWidget(QLabel("Tendencias (subcategorías y términos)"))
        self._trends_view = QPlainTextEdit()
        self._trends_view.setReadOnly(True)
        self._trends_view.setMinimumHeight(140)
        inner_l.addWidget(self._trends_view)

        inner_l.addWidget(QLabel("Anomalías de distribución"))
        self._anom_view = QPlainTextEdit()
        self._anom_view.setReadOnly(True)
        self._anom_view.setMaximumHeight(100)
        inner_l.addWidget(self._anom_view)

        scroll.setWidget(inner)
        root.addWidget(scroll, stretch=1)

        self._status = QLabel("")
        self._status.setWordWrap(True)
        root.addWidget(self._status)

    def set_loading(self, loading: bool, message: str = "") -> None:
        self._btn_refresh.setEnabled(not loading)
        if loading:
            self._status.setText(message or "Cargando insights…")
        else:
            self._status.setText(message)

    def set_error(self, message: str) -> None:
        self.set_loading(False, "")
        self._status.setText(f"Error: {message}")

    def apply_bundle(self, summary: dict[str, Any], gaps: dict[str, Any], trends: dict[str, Any]) -> None:
        self.set_loading(False, "Listo.")
        score = summary.get("system_health_score")
        self._health.setText(f"Salud del sistema: {score:.1f} / 100" if isinstance(score, (int, float)) else "Salud: —")

        dc = summary.get("dataset_coverage") or {}
        cov = dc.get("coverage_ratio_of_known_catalog")
        tot = dc.get("total_clips")
        rep = dc.get("known_subcategories_represented")
        cat = dc.get("known_subcategory_catalog_size")
        if isinstance(cov, (int, float)) and tot is not None:
            self._coverage.setText(
                f"Cobertura catálogo conocido: {100.0 * float(cov):.1f}% "
                f"({rep}/{cat} subcategorías con ≥1 clip) · clips totales: {tot}"
            )
        else:
            self._coverage.setText("Cobertura: —")

        ed = summary.get("embedding_distribution_summary") or {}
        ch = ed.get("chroma_indexed_count")
        sql = ed.get("sqlite_clip_count")
        sr = ed.get("sync_ratio")
        sync_txt = f"sync {float(sr):.0%}" if isinstance(sr, (int, float)) else "sync —"
        self._embed.setText(
            f"SQLite: {sql} clips · Chroma indexados: {ch if ch is not None else '—'} · {sync_txt}"
        )

        gaps_payload = {
            "narrative_gap_patterns": gaps.get("narrative_gap_patterns", [])[:12],
            "weak_retrieval_zones": gaps.get("weak_retrieval_zones", []),
            "search_failure_patterns": gaps.get("search_failure_patterns", []),
            "missing_semantic_clusters_sample": (gaps.get("missing_semantic_clusters") or [])[:40],
        }
        self._gaps_view.setPlainText(json.dumps(gaps_payload, ensure_ascii=False, indent=2))

        trends_payload = {
            "dominant_narrative_pattern": trends.get("dominant_narrative_pattern"),
            "trending_clusters_top": (trends.get("trending_clusters") or [])[:15],
            "most_frequent_semantic_concepts": (trends.get("most_frequent_semantic_concepts") or [])[:20],
            "narrative_function_distribution": trends.get("narrative_function_distribution"),
        }
        self._trends_view.setPlainText(json.dumps(trends_payload, ensure_ascii=False, indent=2))

        anom = summary.get("clip_distribution_anomalies") or []
        self._anom_view.setPlainText(json.dumps(anom, ensure_ascii=False, indent=2))
