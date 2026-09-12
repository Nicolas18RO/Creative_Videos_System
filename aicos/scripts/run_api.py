"""Arranca Uvicorn con el intérprete que instaló el paquete (evita Python global sin ML deps)."""

from __future__ import annotations

import argparse
import logging


def main() -> None:
    parser = argparse.ArgumentParser(description="AI-COS FastAPI (uvicorn)")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--reload", action="store_true", default=True)
    parser.add_argument("--no-reload", action="store_false", dest="reload")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    import uvicorn

    uvicorn.run(
        "aicos.api.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
