"""Zona de arrastrar y soltar para archivos de audio (.mp3 / .wav)."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDragLeaveEvent, QDragMoveEvent, QDropEvent
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget


class AudioDropZone(QWidget):
    """Widget que acepta solo .mp3 / .wav y emite la ruta local del primer archivo válido."""

    audio_dropped = pyqtSignal(str)

    _STYLE_IDLE = """
        AudioDropZone {
            border: 2px dashed #6b7280;
            border-radius: 8px;
            background: #f9fafb;
        }
    """
    _STYLE_HOVER = """
        AudioDropZone {
            border: 2px solid #22c55e;
            border-radius: 8px;
            background: #ecfdf5;
        }
    """
    _STYLE_BUSY = """
        AudioDropZone {
            border: 2px solid #3b82f6;
            border-radius: 8px;
            background: #eff6ff;
        }
    """
    _STYLE_ERROR = """
        AudioDropZone {
            border: 2px solid #ef4444;
            border-radius: 8px;
            background: #fef2f2;
        }
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._processing = False
        self._drag_inside = False

        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 12, 16, 12)
        self._title = QLabel("Suelta aquí un audio para analizarlo")
        self._title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title.setWordWrap(True)
        self._hint = QLabel("Solo MP3 o WAV · se copiará a caché local y se llamará a POST /analyze")
        self._hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._hint.setWordWrap(True)
        self._hint.setStyleSheet("color: #6b7280; font-size: 11px;")
        inner = QHBoxLayout()
        inner.addStretch(1)
        inner.addWidget(self._title, stretch=1)
        inner.addStretch(1)
        lay.addLayout(inner)
        lay.addWidget(self._hint)
        self._apply_idle_visual()

    def set_processing(self, active: bool, message: str | None = None) -> None:
        """Si ``active``, desactiva drops y muestra mensaje de progreso."""
        self._processing = active
        self.setAcceptDrops(not active)
        if active:
            self._title.setText(message or "Analizando audio…")
            self._hint.setText("Espera a que termine la petición a la API.")
            self.setStyleSheet(self._STYLE_BUSY)
        else:
            self._apply_idle_visual()

    def set_success(self, message: str | None = None) -> None:
        """Estado breve de éxito (vuelve a idle al cabo de unos segundos vía llamada externa)."""
        self._processing = False
        self.setAcceptDrops(True)
        self._title.setText(message or "Análisis completado")
        self._hint.setText("Puedes soltar otro archivo cuando quieras.")
        self.setStyleSheet(self._STYLE_IDLE)

    def set_error(self, message: str | None = None) -> None:
        self._processing = False
        self.setAcceptDrops(True)
        self._title.setText(message or "No se pudo analizar el audio")
        self._hint.setText("Suelta aquí un audio para analizarlo")
        self.setStyleSheet(self._STYLE_ERROR)

    def _apply_idle_visual(self) -> None:
        self._title.setText("Suelta aquí un audio para analizarlo")
        self._hint.setText("Solo MP3 o WAV · se copiará a caché local y se llamará a POST /analyze")
        self.setStyleSheet(self._STYLE_IDLE)

    def reset_idle(self) -> None:
        """Restaura texto y estilo por defecto."""
        self._drag_inside = False
        self._apply_idle_visual()

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if self._processing:
            event.ignore()
            return
        if event.mimeData().hasUrls():
            for u in event.mimeData().urls():
                path = u.toLocalFile()
                if path and self._is_allowed_audio(path):
                    event.acceptProposedAction()
                    self._set_drag_hover(True)
                    return
        event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        if self._processing:
            event.ignore()
            return
        if event.mimeData().hasUrls():
            for u in event.mimeData().urls():
                path = u.toLocalFile()
                if path and self._is_allowed_audio(path):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dragLeaveEvent(self, event: QDragLeaveEvent) -> None:
        self._set_drag_hover(False)
        super().dragLeaveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        self._set_drag_hover(False)
        if self._processing:
            event.ignore()
            return
        if not event.mimeData().hasUrls():
            event.ignore()
            return
        for u in event.mimeData().urls():
            path = u.toLocalFile()
            if path and self._is_allowed_audio(path):
                event.acceptProposedAction()
                self.audio_dropped.emit(path)
                return
        event.ignore()

    def _set_drag_hover(self, on: bool) -> None:
        if self._processing:
            return
        self._drag_inside = on
        if on:
            self.setStyleSheet(self._STYLE_HOVER)
        else:
            self.setStyleSheet(self._STYLE_IDLE)

    @staticmethod
    def _is_allowed_audio(path: str) -> bool:
        return Path(path).suffix.lower() in {".mp3", ".wav"}
