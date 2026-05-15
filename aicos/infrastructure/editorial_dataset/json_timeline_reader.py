"""Lectura de timelines JSON (solo I/O y parseo)."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from aicos.application.editorial_dataset.ports import JsonTimelineReadPort

logger = logging.getLogger(__name__)


class JsonTimelineFileReader(JsonTimelineReadPort):
    def load_timeline_document(self, path: Path) -> dict[str, Any]:
        text = path.read_text(encoding="utf-8")
        data = json.loads(text)
        if not isinstance(data, dict):
            raise ValueError("timeline_json_must_be_object")
        logger.debug("timeline_json_loaded path=%s keys=%s", path, list(data.keys()))
        return data
