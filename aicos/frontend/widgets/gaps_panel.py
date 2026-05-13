"""Panel derecho: gap M3 (keywords TikTok, prompts IA) para la escena actual (PRD Fase 2)."""

from __future__ import annotations

from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QGroupBox, QLabel, QVBoxLayout, QWidget


class GapsPanel(QWidget):
    """Muestra el gap persistido asociado a la escena seleccionada, si existe."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        box = QGroupBox("Gaps (M3)")
        lay = QVBoxLayout(self)
        lay.addWidget(box)
        inner = QVBoxLayout(box)
        self._body = QLabel("Selecciona un proyecto y una escena.")
        self._body.setWordWrap(True)
        self._body.setTextFormat(Qt.TextFormat.RichText)
        inner.addWidget(self._body)

    def set_exploration_hint(self, message: str) -> None:
        """Mensaje informativo cuando no hay escena M3 (p. ej. exploración de biblioteca)."""
        self._body.setText(message)

    def set_gap(self, gap: dict[str, Any] | None) -> None:
        if not gap:
            self._body.setText("Sin gap registrado para esta escena (o índice aún no cargado).")
            return
        kws = gap.get("tiktok_keywords") or []
        kw_line = ", ".join(str(k) for k in kws) if kws else "—"
        img = gap.get("ai_image_prompt") or "—"
        mot = gap.get("ai_motion_prompt") or "—"
        tax = gap.get("taxonomy_suggestion") or "—"
        gtype = gap.get("gap_type", "")
        self._body.setText(
            f"<b>Tipo</b>: {gtype}<br><br>"
            f"<b>Keywords TikTok</b><br>{kw_line}<br><br>"
            f"<b>Prompt imagen</b><br>{img}<br><br>"
            f"<b>Prompt movimiento</b><br>{mot}<br><br>"
            f"<b>Sugerencia taxonomía</b><br>{tax}"
        )
