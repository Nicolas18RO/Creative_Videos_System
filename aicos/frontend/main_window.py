"""Ventana principal del dashboard Fase 2 (compone widgets + ``AicosApiClient``)."""

from __future__ import annotations

import os
import sys
from datetime import datetime
from typing import Any

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from aicos.frontend.client import AicosApiClient
from aicos.frontend.utils.audio_staging import stage_audio_file
from aicos.frontend.widgets.audio_drop_zone import AudioDropZone
from aicos.frontend.widgets.decision_panel import DecisionPanel
from aicos.frontend.widgets.gaps_panel import GapsPanel
from aicos.frontend.widgets.insights_panel import InsightsPanel
from aicos.frontend.widgets.library_clips_panel import LibraryClipsPanel
from aicos.frontend.widgets.library_sidebar import LibrarySidebar
from aicos.frontend.widgets.recommendations_strip import RecommendationsStrip
from aicos.frontend.widgets.transcript_panel import TranscriptPanel
from aicos.frontend.workers import AnalyzeAudioTask, JsonTaskThread


class MainWindow(QMainWindow):
    """Layout PRD: barra biblioteca | (transcript | recomendaciones | gaps) + proyectos/escenas."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("AI-COS — Dashboard (Fase 2–4)")
        self.resize(1280, 780)

        base = os.environ.get("AICOS_API_BASE", "http://127.0.0.1:8000").rstrip("/")
        self._client = AicosApiClient(base)
        self._detail: dict[str, Any] | None = None
        self._gaps_by_scene_id: dict[str, dict[str, Any]] = {}
        self._current_project_id: str | None = None
        self._search_preview: list[dict[str, Any]] | None = None
        self._active_thread: JsonTaskThread | None = None
        self._clips_page_size = 50
        self._insights_tab_loaded = False
        self._decisions_tab_loaded = False

        root = QWidget()
        self.setCentralWidget(root)
        main_l = QVBoxLayout(root)

        api_row = QHBoxLayout()
        api_row.addWidget(QLabel("API:"))
        self._api_edit = QLineEdit(self._client.base_url)
        api_row.addWidget(self._api_edit, stretch=1)
        btn_apply = QPushButton("Usar URL")
        btn_apply.clicked.connect(self._on_apply_base)
        api_row.addWidget(btn_apply)
        btn_analyze = QPushButton("Analizar audio (POST /analyze)…")
        btn_analyze.clicked.connect(self._on_analyze_audio)
        api_row.addWidget(btn_analyze)
        main_l.addLayout(api_row)

        self._drop = AudioDropZone()
        self._drop.audio_dropped.connect(self.handle_audio_file)
        main_l.addWidget(self._drop)

        outer = QSplitter(Qt.Orientation.Horizontal)

        left_wrap = QWidget()
        left_col = QVBoxLayout(left_wrap)
        left_col.setContentsMargins(0, 0, 0, 0)
        self._library = LibrarySidebar()
        self._library.manual_search_requested.connect(self._on_manual_library_search)
        left_col.addWidget(self._library)
        self._clips_panel = LibraryClipsPanel(page_size=self._clips_page_size)
        self._clips_panel.load_more_requested.connect(self._on_clips_load_more)
        self._clips_panel.clip_activated.connect(self._on_library_clip_activated)
        left_col.addWidget(self._clips_panel, stretch=1)

        self._insights = InsightsPanel()
        self._insights.recompute_requested.connect(self._load_insights_bundle)

        self._decisions = DecisionPanel()
        self._decisions.reevaluate_requested.connect(self._load_decisions_bundle)

        self._left_tabs = QTabWidget()
        self._left_tabs.addTab(left_wrap, "Biblioteca")
        self._left_tabs.addTab(self._insights, "Insights")
        self._left_tabs.addTab(self._decisions, "Decisiones")
        self._left_tabs.currentChanged.connect(self._on_left_tab_changed)
        outer.addWidget(self._left_tabs)

        center = QWidget()
        cv = QVBoxLayout(center)
        triple = QSplitter(Qt.Orientation.Horizontal)
        self._transcript = TranscriptPanel()
        self._rec_strip = RecommendationsStrip()
        self._rec_strip.feedback_submitted.connect(self._on_feedback)
        self._gaps = GapsPanel()
        triple.addWidget(self._transcript)
        triple.addWidget(self._rec_strip)
        triple.addWidget(self._gaps)
        triple.setSizes([320, 520, 340])
        cv.addWidget(triple)

        btn_row = QHBoxLayout()
        self._btn_research = QPushButton("Re-buscar clips para escena (/search)")
        self._btn_research.clicked.connect(self._on_scene_search)
        self._btn_research.setEnabled(False)
        btn_row.addWidget(self._btn_research)
        btn_row.addStretch(1)
        cv.addLayout(btn_row)

        bottom = QSplitter(Qt.Orientation.Horizontal)
        left_b = QWidget()
        bl = QVBoxLayout(left_b)
        bl.addWidget(QLabel("Proyectos"))
        self._btn_refresh = QPushButton("Refrescar")
        self._btn_refresh.clicked.connect(self._load_projects)
        bl.addWidget(self._btn_refresh)
        self._projects = QListWidget()
        self._projects.currentItemChanged.connect(self._on_project_changed)
        bl.addWidget(self._projects)

        right_b = QWidget()
        br = QVBoxLayout(right_b)
        br.addWidget(QLabel("Escenas"))
        self._scenes = QListWidget()
        self._scenes.currentItemChanged.connect(self._on_scene_changed)
        br.addWidget(self._scenes)

        bottom.addWidget(left_b)
        bottom.addWidget(right_b)
        bottom.setSizes([300, 360])
        cv.addWidget(bottom)

        outer.addWidget(center)
        outer.setSizes([340, 940])
        main_l.addWidget(outer)

        self._startup_library_and_projects()

    def handle_audio_file(self, file_path: str) -> None:
        """Staging local + ``POST /analyze`` en hilo; actualiza paneles con el proyecto persistido."""
        if self._active_thread and self._active_thread.isRunning():
            QMessageBox.warning(self, "Ocupado", "Espera a que termine la petición anterior.")
            return
        try:
            staged_path = stage_audio_file(file_path)
        except (FileNotFoundError, ValueError, OSError) as ex:
            self._drop.set_error(str(ex))
            self.statusBar().showMessage(str(ex), 10000)
            QTimer.singleShot(4500, self._drop.reset_idle)
            return

        project_name = f"Audio drop {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        body: dict[str, Any] = {
            "audio_path": staged_path,
            "project_name": project_name,
            "persist": True,
            "include_clip_search": True,
            "enable_intelligence": True,
        }

        self._drop.set_processing(True, "Analizando audio…")
        self.statusBar().showMessage("Analizando audio…")

        def ok(payload: object) -> None:
            data = payload  # type: ignore[assignment]
            if not isinstance(data, dict):
                self._drop.set_error("Respuesta inesperada del analizador.")
                self.statusBar().showMessage("Error: respuesta inesperada.", 8000)
                QTimer.singleShot(4500, self._drop.reset_idle)
                return
            detail = data.get("detail")
            gaps = data.get("gaps")
            analysis = data.get("analysis") or {}
            if not isinstance(detail, dict) or not isinstance(gaps, dict):
                self._drop.set_error("La API no devolvió detalle de proyecto tras analizar.")
                self.statusBar().showMessage("Análisis incompleto.", 8000)
                QTimer.singleShot(4500, self._drop.reset_idle)
                return
            self._apply_project_detail_and_gaps(detail, gaps)
            pid = str(analysis.get("project_id") or self._current_project_id or "")
            self._load_projects(select_project_id=pid or None)
            self._drop.set_success("Análisis completado")
            self.statusBar().showMessage("Análisis completado.", 8000)
            QTimer.singleShot(3500, self._drop.reset_idle)
            QTimer.singleShot(0, self._refresh_intel_tabs_after_drop)

        def err(msg: str) -> None:
            self._drop.set_error("No se pudo analizar el audio")
            self.statusBar().showMessage(f"Error al analizar: {msg}", 15000)
            QTimer.singleShot(5000, self._drop.reset_idle)

        self._start_thread_instance(AnalyzeAudioTask(self._client, body), ok, err)

    def _refresh_intel_tabs_after_drop(self) -> None:
        """Evita solapar ``JsonTaskThread`` tras encadenar lista de proyectos + insights + decisiones."""
        if self._active_thread and self._active_thread.isRunning():
            QTimer.singleShot(400, self._refresh_intel_tabs_after_drop)
            return
        if self._insights_tab_loaded:
            self._load_insights_bundle(refresh=True)
            QTimer.singleShot(0, self._queue_decisions_refresh_after_drop)
        else:
            QTimer.singleShot(0, self._queue_decisions_refresh_after_drop)

    def _queue_decisions_refresh_after_drop(self) -> None:
        if self._active_thread and self._active_thread.isRunning():
            QTimer.singleShot(400, self._queue_decisions_refresh_after_drop)
            return
        if self._decisions_tab_loaded:
            self._load_decisions_bundle(refresh=True)

    def _apply_project_detail_and_gaps(self, detail: dict[str, Any], gaps: dict[str, Any]) -> None:
        """Rellena escenas, gaps y paneles centrales a partir de ``GET /projects`` + ``GET /gaps``."""
        proj = detail.get("project") or {}
        pid = proj.get("id")
        if pid:
            self._current_project_id = str(pid)
        self._detail = detail
        self._gaps_by_scene_id = {}
        for item in gaps.get("gaps", []) or []:
            g = item.get("gap") or {}
            sid = g.get("scene_id")
            if sid:
                self._gaps_by_scene_id[str(sid)] = g
        self._scenes.blockSignals(True)
        self._scenes.clear()
        for sc in detail.get("scenes", []):
            label = f"{sc['scene_index']} | {sc['narrative_function']} | {str(sc.get('concept', ''))[:50]}"
            it = QListWidgetItem(label)
            it.setData(Qt.ItemDataRole.UserRole, sc["scene_id"])
            self._scenes.addItem(it)
        if self._scenes.count() > 0:
            self._scenes.setCurrentRow(0)
        self._scenes.blockSignals(False)
        self._on_scene_changed(self._scenes.currentItem(), None)

    def _on_left_tab_changed(self, index: int) -> None:
        w = self._left_tabs.widget(index)
        if w is self._insights and not self._insights_tab_loaded:
            self._insights_tab_loaded = True
            self._load_insights_bundle(False)
        if w is self._decisions and not self._decisions_tab_loaded:
            self._decisions_tab_loaded = True
            self._load_decisions_bundle(False)

    def _load_decisions_bundle(self, refresh: bool = False) -> None:
        """Carga ``/decisions/*`` en hilo aparte; ``refresh`` en summary fuerza recálculo en servidor."""
        self._decisions.set_loading(True, "Consultando /decisions …")

        def task() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
            summary = self._client.get_decisions_summary(refresh=refresh)
            lst = self._client.get_decisions_list(limit=150, offset=0, refresh=False)
            impact = self._client.get_decisions_impact(refresh=False)
            return summary, lst, impact

        def ok(payload: tuple[dict[str, Any], dict[str, Any], dict[str, Any]]) -> None:
            summary, lst, impact = payload
            self._decisions.apply_bundle(summary, lst, impact)

        def err(msg: str) -> None:
            self._decisions.set_error(msg)

        self._start_thread(task, ok, err)

    def _load_insights_bundle(self, refresh: bool = False) -> None:
        """Carga ``/insights/*`` en hilo aparte; ``refresh`` solo en summary para invalidar caché del servidor."""
        self._insights.set_loading(True, "Consultando /insights …")

        def task() -> dict[str, Any]:
            return {
                "s": self._client.get_insights_summary(refresh=refresh),
                "g": self._client.get_insights_gaps(refresh=False),
                "t": self._client.get_insights_trends(refresh=False),
            }

        def ok(data: dict[str, Any]) -> None:
            self._insights.apply_bundle(data["s"], data["g"], data["t"])

        def err(msg: str) -> None:
            self._insights.set_error(msg)

        self._start_thread(task, ok, err)

    def _on_apply_base(self) -> None:
        self._client.set_base_url(self._api_edit.text().strip() or self._client.base_url)
        self._api_edit.setText(self._client.base_url)
        self._startup_library_and_projects()

    def _startup_library_and_projects(self) -> None:
        """Encadena stats → clips → proyectos para no solapar ``JsonTaskThread``."""

        def task_stats():
            return self._client.get_library_stats()

        def ok_stats(data: dict[str, Any]) -> None:
            self._library.set_stats(data, None)

            def task_clips():
                return self._client.get_clips(limit=self._clips_page_size, offset=0)

            def ok_clips(payload: dict[str, Any]) -> None:
                self._clips_panel.apply_first_page(payload)
                self._load_projects()

            def err_clips(msg: str) -> None:
                self._clips_panel.set_status_text(f"Error al listar clips: {msg}")
                self._load_projects()

            self._start_thread(task_clips, ok_clips, err_clips)

        def err_stats(msg: str) -> None:
            self._library.set_stats(None, error=msg)
            self._clips_panel.reset()
            self._clips_panel.set_status_text("Sin datos de biblioteca.")
            self._load_projects()

        self._start_thread(task_stats, ok_stats, err_stats)

    def _start_thread(self, fn: Any, on_ok: Any, on_err: Any) -> None:
        self._start_thread_instance(JsonTaskThread(fn), on_ok, on_err)

    def _start_thread_instance(self, thread: JsonTaskThread, on_ok: Any, on_err: Any) -> None:
        if self._active_thread and self._active_thread.isRunning():
            QMessageBox.warning(self, "Ocupado", "Espera a que termine la petición anterior.")
            return
        thread.ok.connect(on_ok)
        thread.err.connect(on_err)
        self._active_thread = thread
        thread.start()

    def _reload_clips_first_page(self) -> None:
        """Recarga la primera página de clips (p. ej. tras operaciones que no reencadenan startup)."""
        self._clips_panel.reset()

        def task():
            return self._client.get_clips(limit=self._clips_page_size, offset=0)

        def ok_page(data: dict[str, Any]) -> None:
            self._clips_panel.apply_first_page(data)

        def err_page(msg: str) -> None:
            self._clips_panel.set_status_text(f"Error al listar clips: {msg}")

        self._start_thread(task, ok_page, err_page)

    def _on_clips_load_more(self, offset: int, limit: int) -> None:
        def task():
            return self._client.get_clips(limit=limit, offset=offset)

        def ok_page(data: dict[str, Any]) -> None:
            self._clips_panel.append_page(data)

        def err_page(msg: str) -> None:
            QMessageBox.warning(self, "Biblioteca", f"No se pudo cargar más clips:\n{msg}")

        self._start_thread(task, ok_page, err_page)

    def _on_library_clip_activated(self, clip: dict[str, Any]) -> None:
        """Exploración: metadatos en transcript + similares vía ``/search`` (sin feedback de escena)."""
        self._transcript.set_library_clip(clip)
        self._gaps.set_exploration_hint(
            "Exploración de biblioteca: los gaps M3 se generan al analizar un guion; "
            "aquí solo inspeccionas el clip y vecinos semánticos."
        )
        q = (clip.get("semantic_excerpt") or clip.get("name") or "").strip()
        if not q:
            self._rec_strip.set_placeholder("Este clip no tiene texto semántico para buscar similares.")
            return
        body = {
            "query": q[:500],
            "narrative_function": clip.get("narrative_function") or "PROBLEM",
            "n_results": 8,
            "candidate_pool_size": 24,
        }

        def task():
            return self._client.post_search(body)

        def ok_search(data: dict[str, Any]) -> None:
            out: list[dict[str, Any]] = []
            for rec in data.get("results", []):
                out.append(
                    {
                        "clip_id": rec.get("clip_id"),
                        "clip_path": rec.get("clip_path", ""),
                        "rank": rec.get("rank", 0),
                        "final_score": rec.get("final_score", 0),
                        "thumbnail_path": rec.get("thumbnail_path"),
                    }
                )
            self._rec_strip.set_recommendations(
                scene_id="",
                recs=out,
                preview=True,
                allow_feedback=False,
            )

        def err_search(msg: str) -> None:
            QMessageBox.warning(self, "Biblioteca", f"Búsqueda por clip:\n{msg}")

        self._start_thread(task, ok_search, err_search)

    def _load_projects(self, *, select_project_id: str | None = None) -> None:
        self._client.set_base_url(self._api_edit.text().strip().rstrip("/") or self._client.base_url)
        self._api_edit.setText(self._client.base_url)

        def task():
            return self._client.list_projects()

        def ok(data: list[dict[str, Any]]) -> None:
            self._projects.clear()
            for p in data:
                it = QListWidgetItem(f"{p.get('name', '')} ({str(p.get('id', ''))[:8]}…)")
                it.setData(Qt.ItemDataRole.UserRole, p.get("id"))
                self._projects.addItem(it)
            if select_project_id:
                self._projects.blockSignals(True)
                for i in range(self._projects.count()):
                    it = self._projects.item(i)
                    rid = it.data(Qt.ItemDataRole.UserRole)
                    if rid is not None and str(rid) == select_project_id:
                        self._projects.setCurrentRow(i)
                        break
                self._projects.blockSignals(False)

        def err(msg: str) -> None:
            QMessageBox.warning(self, "Error", f"No se pudieron cargar proyectos:\n{msg}")

        self._start_thread(task, ok, err)

    def _on_project_changed(self, cur: QListWidgetItem | None, _prev: QListWidgetItem | None) -> None:
        self._scenes.clear()
        self._detail = None
        self._gaps_by_scene_id = {}
        self._search_preview = None
        self._transcript.set_scene(None)
        self._transcript.set_library_clip(None)
        self._gaps.set_gap(None)
        self._rec_strip.set_placeholder("Selecciona una escena.")
        self._btn_research.setEnabled(False)
        if cur is None:
            return
        pid = cur.data(Qt.ItemDataRole.UserRole)
        if not pid:
            return
        self._current_project_id = str(pid)

        def task():
            detail = self._client.get_project(str(pid))
            gaps = self._client.get_gaps(str(pid))
            return detail, gaps

        def ok(payload: object) -> None:
            detail, gaps = payload  # type: ignore[misc]
            self._apply_project_detail_and_gaps(detail, gaps)

        def err(msg: str) -> None:
            QMessageBox.warning(self, "Error", f"Proyecto / gaps:\n{msg}")

        self._start_thread(task, ok, err)

    def _current_scene(self) -> dict[str, Any] | None:
        it = self._scenes.currentItem()
        if not it or not self._detail:
            return None
        sid = it.data(Qt.ItemDataRole.UserRole)
        for sc in self._detail.get("scenes", []):
            if sc["scene_id"] == sid:
                return sc
        return None

    def _on_scene_changed(self, _c: QListWidgetItem | None, _p: QListWidgetItem | None) -> None:
        self._search_preview = None
        sc = self._current_scene()
        self._btn_research.setEnabled(sc is not None)
        self._transcript.set_library_clip(None)
        self._transcript.set_scene(sc)
        if sc:
            self._gaps.set_gap(self._gaps_by_scene_id.get(sc["scene_id"]))
        else:
            self._gaps.set_gap(None)
        self._render_recommendations()

    def _render_recommendations(self) -> None:
        sc = self._current_scene()
        if not sc:
            self._rec_strip.set_placeholder("Selecciona una escena.")
            return
        recs = self._search_preview if self._search_preview is not None else sc.get("recommendations", [])
        norm: list[dict[str, Any]] = []
        for r in recs:
            norm.append(
                {
                    "clip_id": r.get("clip_id"),
                    "clip_path": r.get("clip_path", ""),
                    "rank": r.get("rank", 0),
                    "final_score": r.get("final_score", 0),
                    "thumbnail_path": r.get("thumbnail_path"),
                }
            )
        self._rec_strip.set_recommendations(
            scene_id=str(sc["scene_id"]),
            recs=norm,
            preview=self._search_preview is not None,
            allow_feedback=True,
        )

    def _on_scene_search(self) -> None:
        sc = self._current_scene()
        if not sc:
            QMessageBox.information(self, "Escena", "Selecciona una escena primero.")
            return
        body = {
            "query": sc.get("concept") or sc.get("text", "")[:200],
            "narrative_function": sc.get("narrative_function"),
            "gender_hint": sc.get("gender_hint"),
            "is_hook": bool(sc.get("is_hook")),
            "n_results": 5,
        }

        def task():
            return self._client.post_search(body)

        def ok(data: dict[str, Any]) -> None:
            out: list[dict[str, Any]] = []
            for rec in data.get("results", []):
                out.append(
                    {
                        "clip_id": rec.get("clip_id"),
                        "clip_path": rec.get("clip_path", ""),
                        "rank": rec.get("rank", 0),
                        "final_score": rec.get("final_score", 0),
                        "thumbnail_path": rec.get("thumbnail_path"),
                    }
                )
            self._search_preview = out
            self._render_recommendations()

        def err(msg: str) -> None:
            QMessageBox.warning(self, "Error", f"/search:\n{msg}")

        self._start_thread(task, ok, err)

    def _on_manual_library_search(self, query: str) -> None:
        body = {
            "query": query,
            "narrative_function": "PROBLEM",
            "n_results": 15,
            "candidate_pool_size": 30,
        }

        def task():
            return self._client.post_search(body)

        def ok(data: dict[str, Any]) -> None:
            rows: list[dict[str, Any]] = []
            for rec in data.get("results", []):
                rows.append(
                    {
                        "clip_id": rec.get("clip_id"),
                        "clip_path": rec.get("clip_path", ""),
                        "rank": rec.get("rank", 0),
                        "final_score": rec.get("final_score", 0),
                        "thumbnail_path": rec.get("thumbnail_path"),
                    }
                )
            self._library.set_manual_results(rows)

        def err(msg: str) -> None:
            QMessageBox.warning(self, "Biblioteca", f"Búsqueda:\n{msg}")

        self._start_thread(task, ok, err)

    def _on_feedback(self, scene_id: str, clip_id: str, accepted: bool, rank: int) -> None:
        if not clip_id or not str(scene_id).strip():
            return
        body = {
            "scene_id": scene_id,
            "clip_id": clip_id,
            "accepted": accepted,
            "rank": rank,
        }

        def task():
            return self._client.post_feedback(body)

        def ok(_data: object) -> None:
            QMessageBox.information(self, "OK", "Feedback guardado.")
            if self._current_project_id:
                self._reload_current_project()

        def err(msg: str) -> None:
            QMessageBox.warning(self, "Error", f"Feedback:\n{msg}")

        self._start_thread(task, ok, err)

    def _reload_current_project(self) -> None:
        pid = self._current_project_id
        if not pid:
            return
        cur_scene = self._scenes.currentItem()
        sid_keep = cur_scene.data(Qt.ItemDataRole.UserRole) if cur_scene else None

        def task():
            detail = self._client.get_project(pid)
            gaps = self._client.get_gaps(pid)
            return detail, gaps

        def ok(payload: object) -> None:
            detail, gaps = payload  # type: ignore[misc]
            self._detail = detail
            self._gaps_by_scene_id = {}
            for item in gaps.get("gaps", []) or []:
                g = item.get("gap") or {}
                sid = g.get("scene_id")
                if sid:
                    self._gaps_by_scene_id[str(sid)] = g
            self._scenes.blockSignals(True)
            self._scenes.clear()
            sel_row = 0
            for i, sc in enumerate(detail.get("scenes", [])):
                label = f"{sc['scene_index']} | {sc['narrative_function']} | {str(sc.get('concept', ''))[:50]}"
                it = QListWidgetItem(label)
                it.setData(Qt.ItemDataRole.UserRole, sc["scene_id"])
                self._scenes.addItem(it)
                if sid_keep and sc["scene_id"] == sid_keep:
                    sel_row = i
            self._scenes.setCurrentRow(sel_row)
            self._scenes.blockSignals(False)
            self._on_scene_changed(self._scenes.currentItem(), None)

        def err(msg: str) -> None:
            QMessageBox.warning(self, "Error", msg)

        self._start_thread(task, ok, err)

    def _on_analyze_audio(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Audio del creativo",
            "",
            "Audio (*.mp3 *.wav);;Todos (*.*)",
        )
        if not path:
            return
        project_name, dlg_ok = QInputDialog.getText(
            self, "Proyecto", "Nombre del proyecto:", text="Nuevo creativo"
        )
        if not dlg_ok:
            return
        body = {
            "audio_path": path,
            "project_name": project_name or "Proyecto",
            "persist": True,
            "include_clip_search": True,
        }

        def task():
            return self._client.post_analyze(body)

        def ok(_data: object) -> None:
            QMessageBox.information(self, "Análisis", "Análisis completado y persistido (si la API no falló).")
            self._load_projects()

        def err(msg: str) -> None:
            QMessageBox.warning(self, "Análisis", f"/analyze:\n{msg}")

        self._start_thread(task, ok, err)
