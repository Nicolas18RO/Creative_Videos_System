"""Generación local de keywords TikTok y prompts (plantillas deterministas)."""

from __future__ import annotations

import re

from aicos.models.schemas import Scene


def _slug(s: str, *, max_len: int = 48) -> str:
    x = re.sub(r"[^\w\s-]", " ", s, flags=re.UNICODE).strip().lower()
    x = re.sub(r"\s+", "_", x)
    return x[:max_len].strip("_") or "tema"


def generate_tiktok_keywords_local(
    scene: Scene,
    *,
    product_category: str,
    target_audience: str,
) -> list[str]:
    """Lista corta de búsquedas estilo TikTok sin LLM."""
    concept = (scene.concept or scene.text or "").strip()[:200]
    nf = (scene.narrative_function or "PROBLEM").upper()
    gh = (scene.gender_hint or "any").upper()
    base = _slug(concept, max_len=40)
    pc = _slug(product_category, max_len=24) or "salud"
    aud = _slug(target_audience, max_len=24) or "adultos"
    return [
        f"{base} testimonio",
        f"{base} antes despues",
        f"{nf.lower()} {base} ugc",
        f"{base} {pc}",
        f"routine {base}",
        f"{aud} {base} tips",
        f"{base} viral hack",
        f"{gh} {base} story",
    ][:8]


def generate_image_prompt_local(scene: Scene, *, product_category: str) -> str:
    """Prompt de imagen UGC realista (plantilla)."""
    concept = (scene.concept or scene.text or "").strip()[:300]
    nf = scene.narrative_function or "PROBLEM"
    gh = scene.gender_hint or "neutral"
    pc = product_category or "wellness"
    return (
        f"Smartphone selfie UGC, natural soft light, kitchen or living room, "
        f"authentic {gh} subject mid-40s, subtle smile, eye contact with lens. "
        f"Theme: {concept}. Narrative beat: {nf}. Product vibe: {pc}. "
        f"No text overlay, no watermark, photorealistic, shallow depth of field."
    )


def generate_motion_prompt_local(scene: Scene) -> str:
    """Prompt de movimiento corto (plantilla)."""
    concept = (scene.concept or scene.text or "").strip()[:200]
    return (
        f"Handheld micro-movement 3-4s, gentle push-in, organic breathing camera, "
        f"natural light flicker subtle. Subject discusses: {concept}. "
        f"No hard whip pans, no flashy transitions."
    )
