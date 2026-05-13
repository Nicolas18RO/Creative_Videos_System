"""CLI: analizar un MP3 y volcar JSON a stdout o archivo."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

from aicos.modules.script_analyzer import analyze_audio

logger = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="AI-COS: analizar guion desde audio (M1+M2+M3).")
    parser.add_argument("audio", type=Path, help="Ruta al MP3/WAV")
    parser.add_argument("-o", "--output", type=Path, default=None, help="JSON de salida (default: stdout)")
    parser.add_argument("--project-name", default="CLI Project")
    parser.add_argument("--product-category", default="salud/bienestar")
    parser.add_argument("--target-audience", default="adultos 35-55")
    parser.add_argument("--no-search", action="store_true", help="Omitir búsqueda de clips (solo M1+M3 heurístico)")
    parser.add_argument(
        "--no-intelligence",
        action="store_true",
        help="Búsqueda legacy sin memoria (clip_recommender directo).",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)

    async def _run():
        return await analyze_audio(
            args.audio,
            project_name=args.project_name,
            product_category=args.product_category,
            target_audience=args.target_audience,
            include_clip_search=not args.no_search,
            enable_intelligence=not args.no_intelligence,
        )

    result = asyncio.run(_run())
    payload = result.model_dump(mode="json")
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(text, encoding="utf-8")
        logger.info("Escrito %s", args.output)
    else:
        sys.stdout.write(text + "\n")


if __name__ == "__main__":
    main()
