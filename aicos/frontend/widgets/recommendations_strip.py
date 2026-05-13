"""Panel central: miniaturas y scores de recomendaciones por escena (PRD Fase 2)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class RecommendationsStrip(QWidget):
    """Tarjetas horizontales con thumbnail, score y feedback."""

    feedback_submitted = pyqtSignal(str, str, bool, int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        lay = QVBoxLayout(self)
        self._hint = QLabel("Selecciona proyecto y escena.")
        lay.addWidget(self._hint)
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._host = QWidget()
        self._cards_layout = QHBoxLayout(self._host)
        self._cards_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self._scroll.setWidget(self._host)
        lay.addWidget(self._scroll, stretch=1)

    def clear_cards(self) -> None:
        while self._cards_layout.count():
            w = self._cards_layout.takeAt(0).widget()
            if w:
                w.deleteLater()

    def set_placeholder(self, message: str) -> None:
        """Sin escena seleccionada o estado inicial."""
        self.clear_cards()
        self._hint.setText(message)

    def set_recommendations(
        self,
        *,
        scene_id: str,
        recs: list[dict[str, Any]],
        preview: bool,
        allow_feedback: bool = True,
    ) -> None:
        self.clear_cards()
        if preview and not scene_id:
            self._hint.setText("Vista: similares semánticos (exploración de biblioteca).")
        elif preview:
            self._hint.setText("Vista: búsqueda nueva (no persistida en el proyecto).")
        else:
            n = len(recs)
            self._hint.setText(f"Recomendaciones persistidas: {n}")

        for rec in recs:
            card = QFrame()
            card.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
            cv = QVBoxLayout(card)
            img = QLabel()
            img.setFixedSize(168, 98)
            img.setAlignment(Qt.AlignmentFlag.AlignCenter)
            thumb = rec.get("thumbnail_path") or ""
            if thumb and Path(thumb).is_file():
                pm = QPixmap(thumb)
                if not pm.isNull():
                    img.setPixmap(pm.scaled(160, 90, Qt.AspectRatioMode.KeepAspectRatio))
            else:
                img.setText("Sin miniatura")
            cv.addWidget(img)
            score = rec.get("final_score", 0)
            rank = int(rec.get("rank", 0) or 0)
            cv.addWidget(QLabel(f"Rank {rank} | score {float(score):.2f}"))
            path_l = QLabel((rec.get("clip_path") or "")[:42] + "…")
            path_l.setWordWrap(True)
            cv.addWidget(path_l)
            clip_id = str(rec.get("clip_id", "") or "")
            if allow_feedback and scene_id:
                btn_yes = QPushButton("Aceptar")
                btn_no = QPushButton("Rechazar")
                btn_yes.clicked.connect(
                    lambda _checked=False, sid=scene_id, cid=clip_id, r=rank: self._emit_fb(sid, cid, True, r)
                )
                btn_no.clicked.connect(
                    lambda _checked=False, sid=scene_id, cid=clip_id, r=rank: self._emit_fb(sid, cid, False, r)
                )
                cv.addWidget(btn_yes)
                cv.addWidget(btn_no)
            self._cards_layout.addWidget(card)

    def _emit_fb(self, scene_id: str, clip_id: str, accepted: bool, rank: int) -> None:
        if clip_id:
            self.feedback_submitted.emit(scene_id, clip_id, accepted, rank)
