"""Punto de entrada del dashboard PyQt6 (Fase 2).

La UI vive en ``main_window`` y los widgets bajo ``frontend/widgets/``.
La comunicación con el dominio es solo vía HTTP (`AicosApiClient` → FastAPI local).

Ejecutar (con API en marcha: ``uvicorn aicos.api.main:app``)::

    aicos-dashboard
    python -m aicos.frontend.dashboard
"""

from __future__ import annotations

import sys

try:
    from PyQt6.QtWidgets import QApplication
except ImportError as e:
    raise SystemExit("PyQt6 no está instalado. Ejecuta: pip install 'aicos[ui]'") from e


def main() -> None:
    from aicos.frontend.main_window import MainWindow

    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
