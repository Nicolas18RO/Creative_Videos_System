"""Abstracción de chat completions (OpenAI) para rutas opcionales; desactivada en modo local-first."""

from __future__ import annotations

import base64
import logging
import os
from pathlib import Path

from openai import AsyncOpenAI, OpenAI

from aicos.config import Settings, get_config

logger = logging.getLogger(__name__)

_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


def _read_prompt(name: str) -> str:
    p = _PROMPTS_DIR / name
    if not p.is_file():
        raise FileNotFoundError(str(p))
    return p.read_text(encoding="utf-8")


class LLMService:
    """Cliente OpenAI síncrono y asíncrono (solo si ``runtime`` permite nube)."""

    def __init__(self, api_key: str | None = None) -> None:
        cfg = get_config()
        rt = cfg.runtime
        self._disabled = bool(rt.local_only or not rt.use_openai or rt.offline_mode)
        if self._disabled:
            self._sync = None
            self._async = None
            self._model = cfg.llm.model
            self._vision_model = cfg.vision.model
            self._temperature = cfg.llm.temperature
            self._max_tokens = cfg.llm.max_tokens
            logger.info(
                "LLMService en modo local-first (sin cliente OpenAI). "
                "runtime.local_only=%s use_openai=%s",
                rt.local_only,
                rt.use_openai,
            )
            return

        settings = Settings()
        key = api_key or settings.openai_api_key or os.environ.get("OPENAI_API_KEY")
        if not key:
            raise RuntimeError(
                "Falta OPENAI_API_KEY (o AICOS_OPENAI_API_KEY) para llamadas al LLM."
            )
        self._model = cfg.llm.model
        self._vision_model = cfg.vision.model
        self._temperature = cfg.llm.temperature
        self._max_tokens = cfg.llm.max_tokens
        self._sync = OpenAI(api_key=key)
        self._async = AsyncOpenAI(api_key=key)

    def _require_cloud(self, method: str) -> None:
        if self._disabled or self._sync is None:
            raise RuntimeError(
                f"LLMService.{method}: OpenAI deshabilitado (runtime.local_only / offline_mode). "
                "Usa heurísticas locales o configura runtime.use_openai=true y API key."
            )

    def complete(self, system: str, user: str) -> str:
        """Una respuesta de chat (síncrono)."""
        self._require_cloud("complete")
        resp = self._sync.chat.completions.create(
            model=self._model,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        choice = resp.choices[0].message.content or ""
        return choice.strip()

    async def acomplete(self, system: str, user: str) -> str:
        """Una respuesta de chat (asíncrono)."""
        self._require_cloud("acomplete")
        resp = await self._async.chat.completions.create(
            model=self._model,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        choice = resp.choices[0].message.content or ""
        return choice.strip()

    async def extract_concept_llm(self, text: str, narrative_function: str) -> str:
        """Extrae concepto visual en inglés (2–5 palabras) vía plantilla."""
        self._require_cloud("extract_concept_llm")
        tmpl = _read_prompt("concept_extraction.txt")
        user = tmpl.format(text=text.strip()[:2000], narrative_function=narrative_function)
        system = "Sigues el formato pedido al pie de la letra."
        out = await self.acomplete(system, user)
        return " ".join(out.split()[:8]).strip('"\'')

    async def gap_tiktok_keywords(
        self,
        *,
        concept: str,
        narrative_function: str,
        product_category: str,
        target_audience: str,
    ) -> list[str]:
        self._require_cloud("gap_tiktok_keywords")
        tmpl = _read_prompt("gap_keywords.txt")
        user = tmpl.format(
            concept=concept,
            narrative_function=narrative_function,
            product_category=product_category,
            target_audience=target_audience,
        )
        system = "Eres un experto en UGC y TikTok para performance ads."
        raw = await self.acomplete(system, user)
        lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
        return lines[:8]

    async def gap_image_prompt(
        self,
        *,
        concept: str,
        narrative_function: str,
        gender_preference: str,
    ) -> str:
        self._require_cloud("gap_image_prompt")
        tmpl = _read_prompt("image_prompt.txt")
        user = tmpl.format(
            concept=concept,
            narrative_function=narrative_function,
            gender_preference=gender_preference or "any",
        )
        system = "Generas prompts de imagen realistas estilo UGC."
        return await self.acomplete(system, user)

    async def vision_text_response(self, system: str, image_path: Path) -> str:
        """Una respuesta de modelo de visión (imagen + instrucción en system)."""
        self._require_cloud("vision_text_response")
        data = image_path.read_bytes()
        b64 = base64.standard_b64encode(data).decode("ascii")
        ext = image_path.suffix.lower()
        mime = "image/jpeg" if ext in (".jpg", ".jpeg") else "image/png"
        resp = await self._async.chat.completions.create(
            model=self._vision_model,
            temperature=self._temperature,
            max_tokens=1200,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": system},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime};base64,{b64}"},
                        },
                    ],
                }
            ],
        )
        return (resp.choices[0].message.content or "").strip()
