"""Hilos de trabajo para no bloquear el hilo UI (peticiones HTTP, etc.)."""

from __future__ import annotations

from typing import Any

from PyQt6.QtCore import QThread, pyqtSignal

from aicos.frontend.client import AicosApiClient


class JsonTaskThread(QThread):
    """Ejecuta una función que devuelve un valor serializable en un hilo aparte."""

    ok = pyqtSignal(object)
    err = pyqtSignal(str)

    def __init__(self, fn: Any) -> None:
        super().__init__()
        self._fn = fn

    def run(self) -> None:
        try:
            self.ok.emit(self._fn())
        except Exception as ex:
            self.err.emit(str(ex))


def analyze_audio_and_fetch(client: AicosApiClient, body: dict[str, Any]) -> dict[str, Any]:
    """Ejecuta ``POST /analyze`` y carga detalle + gaps del proyecto para la UI.

    Todo el trabajo I/O ocurre en el hilo que invoque esta función (p. ej. ``JsonTaskThread``).

    Returns:
        Diccionario con claves ``analysis`` (respuesta cruda de /analyze), ``detail`` y ``gaps``
        (formato de ``GET /projects/{id}`` y ``GET /gaps/{id}``), o ``None`` en ``detail``/``gaps``
        si falta ``project_id`` en la respuesta.
    """
    analysis = client.post_analyze(body)
    pid = analysis.get("project_id")
    if not pid:
        return {"analysis": analysis, "detail": None, "gaps": None}
    pid_str = str(pid)
    detail = client.get_project(pid_str)
    gaps = client.get_gaps(pid_str)
    return {"analysis": analysis, "detail": detail, "gaps": gaps}


class AnalyzeAudioTask(JsonTaskThread):
    """Hilo que analiza audio vía API y trae el detalle persistido para refrescar paneles."""

    def __init__(self, client: AicosApiClient, body: dict[str, Any]) -> None:
        super().__init__(lambda: analyze_audio_and_fetch(client, body))
