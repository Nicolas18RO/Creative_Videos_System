"""OpenCLIP con codificación por lotes (torch import perezoso)."""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class OpenClipBatchImageEncoder:
    """Codifica múltiples JPEG en un forward cuando es posible."""

    def __init__(self, *, model_name: str, pretrained: str) -> None:
        self._model_name = model_name
        self._pretrained = pretrained
        self._model = None
        self._preprocess = None
        self._device = None

    def model_tag(self) -> str:
        return f"openclip/{self._model_name}/{self._pretrained}"

    def _ensure(self) -> bool:
        if self._model is not None:
            return True
        try:
            import torch
            import open_clip
        except ImportError as e:
            logger.warning("[OpenCLIPBatch] import_failed: %s", e)
            return False
        try:
            self._model, _, self._preprocess = open_clip.create_model_and_transforms(
                self._model_name,
                pretrained=self._pretrained,
            )
            self._device = "cuda" if torch.cuda.is_available() else "cpu"
            self._model = self._model.to(self._device)
            self._model.eval()
            logger.info("[OpenCLIPBatch] loaded tag=%s device=%s", self.model_tag(), self._device)
            return True
        except Exception as e:
            logger.warning("[OpenCLIPBatch] load_failed: %s", e)
            return False

    def encode_image_paths_batch(self, image_paths: list[str]) -> list[list[float] | None]:
        if not image_paths:
            return []
        if not self._ensure():
            return [None] * len(image_paths)
        try:
            import torch
            from PIL import Image

            tensors: list = []
            valid_indices: list[int] = []
            for i, p in enumerate(image_paths):
                path = Path(p)
                if not path.is_file():
                    continue
                try:
                    img = Image.open(path).convert("RGB")
                    tensors.append(self._preprocess(img))
                    valid_indices.append(i)
                except Exception as e:
                    logger.warning("[OpenCLIPBatch] preprocess_fail path=%s: %s", path, e)

            out: list[list[float] | None] = [None] * len(image_paths)
            if not tensors:
                return out

            batch = torch.stack(tensors, dim=0).to(self._device)
            with torch.no_grad():
                emb = self._model.encode_image(batch)
                emb = emb / emb.norm(dim=-1, keepdim=True)
            rows = emb.cpu().tolist()
            for j, orig_i in enumerate(valid_indices):
                out[orig_i] = [float(x) for x in rows[j]]
            return out
        except Exception as e:
            logger.warning("[OpenCLIPBatch] encode_failed: %s", e)
            return [None] * len(image_paths)
