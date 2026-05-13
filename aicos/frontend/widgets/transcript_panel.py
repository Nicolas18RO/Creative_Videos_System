"""Panel izquierdo: texto de escena, concepto, función narrativa e indicador de hook (PRD Fase 2)."""

from __future__ import annotations

from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QGroupBox, QLabel, QVBoxLayout, QWidget


class TranscriptPanel(QWidget):
    """Muestra el contenido semántico de la escena seleccionada."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        box = QGroupBox("Transcript / escena")
        lay = QVBoxLayout(self)
        lay.addWidget(box)
        inner = QVBoxLayout(box)
        self._meta = QLabel("—")
        self._meta.setWordWrap(True)
        self._text = QLabel("")
        self._text.setWordWrap(True)
        self._text.setTextFormat(Qt.TextFormat.RichText)
        inner.addWidget(self._meta)
        inner.addWidget(self._text)

    def set_scene(self, scene: dict[str, Any] | None) -> None:
        if not scene:
            self._meta.setText("—")
            self._text.setText("")
            return
        hook = "Sí" if scene.get("is_hook") else "No"
        nf = scene.get("narrative_function", "")
        gh = scene.get("gender_hint") or "—"
        idx = scene.get("scene_index", "?")
        self._meta.setText(
            f"Escena #{idx} · Función: {nf} · Hook: {hook} · Género (pista): {gh}"
        )
        concept = scene.get("concept") or ""
        body = scene.get("text") or ""
        self._text.setText(f"<b>Concepto</b><br>{concept}<br><br><b>Texto</b><br>{body}")

    def set_library_clip(self, clip: dict[str, Any] | None) -> None:
        """Vista de inspección de un clip desde la biblioteca (sin escena de proyecto)."""
        if not clip:
            self._meta.setText("—")
            self._text.setText("")
            return
        nf = clip.get("narrative_function") or "—"
        sub = clip.get("subcategory") or "—"
        sid = clip.get("scene_id")
        esc = f"Escena vinculada: {sid[:10]}…" if sid else "Sin escena de proyecto vinculada"
        h = clip.get("file_hash") or "—"
        self._meta.setText(
            f"Biblioteca · <b>{clip.get('name', '')}</b><br>"
            f"Función: {nf} · Subcategoría: {sub}<br>"
            f"{esc}<br>Hash: {str(h)[:20]}{'…' if len(str(h)) > 20 else ''}"
        )
        rel = clip.get("relative_path") or ""
        excerpt = clip.get("semantic_excerpt") or ""
        tags = clip.get("tags") or ""
        dur = clip.get("duration_ms")
        dtxt = f"{int(dur) // 1000} s" if isinstance(dur, int) else "—"
        self._text.setText(
            f"<b>Ruta</b><br>{rel}<br><br>"
            f"<b>Duración</b> {dtxt}<br><br>"
            f"<b>Tags</b><br>{tags or '—'}<br><br>"
            f"<b>Texto semántico (extracto)</b><br>{excerpt or '—'}"
        )
