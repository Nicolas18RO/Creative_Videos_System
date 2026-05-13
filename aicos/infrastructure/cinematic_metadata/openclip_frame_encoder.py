"""Codificador OpenCLIP opcional (torch + open_clip; dependencia extra ``open-clip-torch``)."""

from __future__ import annotations

import logging
from pathlib import Path

from aicos.application.cinematic_metadata.ports import VisualFrameEmbeddingPort

logger = logging.getLogger(__name__)


class OpenClipFrameEncoder(VisualFrameEmbeddingPort):
    """Embeddings de imagen vía OpenCLIP; inicialización perezosa."""

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
            logger.warning("[OpenCLIP] import_failed: %s", e)
            return False
        try:
            self._model, _, self._preprocess = open_clip.create_model_and_transforms(
                self._model_name,
                pretrained=self._pretrained,
            )
            self._device = "cuda" if torch.cuda.is_available() else "cpu"
            self._model = self._model.to(self._device)
            self._model.eval()
            logger.info("[OpenCLIP] model_loaded tag=%s device=%s", self.model_tag(), self._device)
            return True
        except Exception as e:
            logger.warning("[OpenCLIP] load_failed: %s", e)
            return False

    def encode_image_path(self, image_path: str) -> list[float] | None:
        p = Path(image_path)
        if not p.is_file():
            return None
        if not self._ensure():
            return None
        try:
            import torch
            from PIL import Image

            img = Image.open(p).convert("RGB")
            tensor = self._preprocess(img).unsqueeze(0).to(self._device)
            with torch.no_grad():
                emb = self._model.encode_image(tensor)
                emb = emb / emb.norm(dim=-1, keepdim=True)
            return [float(x) for x in emb[0].cpu().tolist()]
        except Exception as e:
            logger.warning("[OpenCLIP] encode_failed path=%s: %s", p, e)
            return None
