"""Segmentación de transcript en escenas + detección de hook y función narrativa (M1)."""

from __future__ import annotations

import logging
import re
import uuid
from dataclasses import dataclass

from aicos.config import get_config
from aicos.models.schemas import Scene, Transcript, TranscriptWord

logger = logging.getLogger(__name__)


@dataclass
class _W:
    start_ms: int
    end_ms: int
    word: str


def _flatten_words(transcript: Transcript) -> list[_W]:
    words: list[_W] = []
    for seg in transcript.segments:
        if seg.words:
            for w in seg.words:
                if w.word.strip():
                    words.append(_W(w.start_ms, w.end_ms, w.word.strip()))
            continue
        # Sin palabras: repartir el texto del segmento de forma uniforme
        toks = [t for t in re.split(r"\s+", seg.text.strip()) if t]
        if not toks:
            continue
        span = max(1, seg.end_ms - seg.start_ms)
        step = span // len(toks)
        for i, t in enumerate(toks):
            s = seg.start_ms + i * step
            e = seg.start_ms + (i + 1) * step if i < len(toks) - 1 else seg.end_ms
            words.append(_W(s, e, t))
    return words


HOOK_KEYWORDS: dict[str, float] = {
    "dolor": 0.15,
    "sufres": 0.15,
    "sufrir": 0.15,
    "problema": 0.10,
    "secreto": 0.20,
    "nadie": 0.15,
    "error": 0.15,
    "peligro": 0.20,
    "descubre": 0.15,
    "solución": 0.10,
    "funciona": 0.10,
    "millones": 0.10,
    "años": 0.05,
    "%": 0.10,
    "¿": 0.20,
    "?": 0.20,
}


def _hook_score(text: str, start_ms: int, hook_window_ms: int) -> float:
    tl = text.lower()
    score = 0.0
    if start_ms < hook_window_ms and hook_window_ms > 0:
        score += 0.30 * (1.0 - start_ms / hook_window_ms)
    for kw, w in HOOK_KEYWORDS.items():
        if kw in tl:
            score += w
    return min(1.0, score)


def _infer_narrative_function(text: str, start_ms: int, total_ms: int) -> str:
    if total_ms <= 0:
        return "PROBLEM"
    ratio = start_ms / total_ms
    tl = text.lower()
    if ratio < 0.15:
        return "HOOK"
    if ratio > 0.85:
        if any(x in tl for x in ("compra", "orden", "link", "oferta", "ahora", "cta", "descuento")):
            return "CTA"
    problem_kw = ("dolor", "sufr", "problem", "difícil", "mal", "peor", "síntoma", "malestar")
    benefit_kw = ("ahora", "puedes", "normal", "fácil", "cómod", "solución", "natural", "ayuda")
    result_kw = ("result", "mejor", "transform", "recuper", "logr", "antes", "después")
    authority_kw = ("doctor", "estudio", "científic", "laborator", "comprob", "clínico", "médico")
    for kw in problem_kw:
        if kw in tl:
            return "PROBLEM"
    for kw in result_kw:
        if kw in tl:
            return "RESULT"
    for kw in authority_kw:
        if kw in tl:
            return "AUTHORITY"
    for kw in benefit_kw:
        if kw in tl:
            return "BENEFIT"
    if ratio < 0.40:
        return "PROBLEM"
    if ratio < 0.70:
        return "BENEFIT"
    return "RESULT"


def _gender_hint_from_text(text: str) -> str | None:
    tl = text.lower()
    if any(x in tl for x in (" mujer", "mujeres", "femen", "ella ")):
        return "F"
    if any(x in tl for x in (" hombre", "hombres", "mascul", "él ")):
        return "M"
    return None


def segment(transcript: Transcript) -> list[Scene]:
    """Divide el transcript en escenas de ~2.5s con cortes en pausas o puntuación."""
    cfg = get_config().segmentation
    target = cfg.target_duration_ms
    silence = cfg.silence_threshold_ms
    hook_win = cfg.hook_window_ms
    min_dur = cfg.min_duration_ms

    words = _flatten_words(transcript)
    if not words:
        logger.warning("Transcript sin palabras segmentables")
        return []

    scenes: list[Scene] = []
    i = 0
    total_ms = transcript.duration_ms or words[-1].end_ms
    scene_index = 0

    while i < len(words):
        start_ms = words[i].start_ms
        j = i
        while j < len(words) and words[j].end_ms - start_ms < target:
            j += 1
        if j == i:
            j = i + 1
        cut = j - 1
        for k in range(j - 1, i, -1):
            wk = words[k].word
            if wk.endswith((".", "?", "!", ",")):
                cut = k
                break
            if k < len(words) - 1:
                gap = words[k + 1].start_ms - words[k].end_ms
                if gap >= silence:
                    cut = k
                    break
        chunk = words[i : cut + 1]
        if not chunk:
            chunk = [words[i]]
            cut = i
        text = " ".join(w.word for w in chunk)
        end_ms = chunk[-1].end_ms
        dur = max(0, end_ms - start_ms)
        if dur < min_dur and cut < len(words) - 1:
            cut = min(len(words) - 1, cut + 1)
            chunk = words[i : cut + 1]
            text = " ".join(w.word for w in chunk)
            end_ms = chunk[-1].end_ms
            dur = max(0, end_ms - start_ms)

        nf = _infer_narrative_function(text, start_ms, total_ms)
        hscore = _hook_score(text, start_ms, hook_win)
        is_hook = start_ms < hook_win and hscore >= 0.45
        gh = _gender_hint_from_text(text)

        scenes.append(
            Scene(
                scene_id=str(uuid.uuid4()),
                scene_index=scene_index,
                start_ms=start_ms,
                end_ms=end_ms,
                duration_ms=dur,
                text=text,
                narrative_function=nf,
                is_hook=is_hook,
                hook_score=hscore,
                gender_hint=gh,
            )
        )
        scene_index += 1
        i = cut + 1

    return scenes
