"""Detección emocional por léxico y heurísticas (local, determinista)."""

from __future__ import annotations

import re
from dataclasses import dataclass

from aicos.domain.cinematic.entities import EmotionAnalysis
from aicos.domain.cinematic.enums import EmotionType


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").lower()).strip()


_LEXICON: list[tuple[EmotionType, tuple[str, ...], float]] = [
    (EmotionType.FEAR, ("miedo", "temor", "afraid", "fear", "peligro", "danger"), 0.75),
    (EmotionType.URGENCY, ("hoy", "today", "última", "last chance", "termina", "expires", "now", "ya"), 0.72),
    (EmotionType.TRUST, ("confianza", "trust", "garantía", "guarantee", "seguro", "safe"), 0.68),
    (EmotionType.JOY, ("feliz", "happy", "celebra", "celebrate", "alegría", "joy"), 0.7),
    (EmotionType.SADNESS, ("triste", "sad", "llor", "cry", "dolor emocional"), 0.65),
    (EmotionType.CURIOSITY, ("¿por qué", "why", "secret", "secreto", "descubre", "find out"), 0.66),
    (EmotionType.EXCITEMENT, ("increíble", "amazing", "wow", "emocion", "excited"), 0.74),
    (EmotionType.RELIEF, ("alivio", "relief", "por fin", "finally", "respira", "breathe"), 0.62),
    (EmotionType.ANXIETY, ("ansiedad", "anxiety", "nervios", "nervous", "worried"), 0.7),
    (EmotionType.SURPRISE, ("sorpresa", "surprise", "no lo vas a creer", "can't believe"), 0.72),
    (EmotionType.CONFIDENCE, ("seguro que", "certain", "garantizado", "proven"), 0.64),
    (EmotionType.ASPIRATION, ("sueña", "dream", "luxury", "lujo", "premium", "next level"), 0.63),
    (EmotionType.EMPATHY, ("entiendo", "i understand", "te escucho", "i hear you"), 0.6),
    (EmotionType.TENSION, ("suspense", "tensión", "edge", "no mires", "don't look away"), 0.68),
    (EmotionType.DESIRE, ("quieres", "you want", "imagina tener", "wish"), 0.65),
    (EmotionType.PAIN, ("duele", "hurts", "frustr", "struggle", "sufres", "suffer"), 0.7),
    (EmotionType.HOPE, ("esperanza", "hope", "mañana mejor", "brighter"), 0.62),
    (EmotionType.MOTIVATION, ("tú puedes", "you can", "empieza", "start now", "vamos", "let's go"), 0.7),
]


@dataclass(slots=True)
class RuleBasedEmotionAnalyzer:
    """Analizador emocional sin embeddings (modo determinista)."""

    def analyze(self, transcript: str, scene_text: str, pacing_hint: str | None = None) -> EmotionAnalysis:
        blob = _norm(f"{transcript} {scene_text}")
        scores: dict[EmotionType, float] = {}
        for emo, patterns, base in _LEXICON:
            hits = sum(1 for p in patterns if p in blob)
            if hits:
                scores[emo] = scores.get(emo, 0.0) + base + 0.05 * min(hits, 4)
        if not scores:
            intensity = 0.35
            if pacing_hint and pacing_hint.upper() == "FAST":
                intensity = 0.55
            return EmotionAnalysis(
                primary_emotion=EmotionType.NEUTRAL,
                secondary_emotions=(),
                emotional_intensity=intensity,
                emotional_arc_position="UNKNOWN",
                energy_curve="flat",
                emotional_transition="none",
            )
        primary = max(scores, key=scores.get)
        secondaries = sorted(
            ((e, s) for e, s in scores.items() if e != primary),
            key=lambda x: x[1],
            reverse=True,
        )[:3]
        intensity = min(0.98, scores[primary] / 1.2)
        arc = "RISING" if intensity > 0.72 else "OPENING" if intensity < 0.45 else "MID"
        energy = "rising" if primary in (EmotionType.EXCITEMENT, EmotionType.URGENCY, EmotionType.FEAR) else "steady"
        if pacing_hint and pacing_hint.upper() == "FAST":
            energy = "spiky"
        return EmotionAnalysis(
            primary_emotion=primary,
            secondary_emotions=tuple(e for e, _ in secondaries),
            emotional_intensity=round(intensity, 3),
            emotional_arc_position=arc,
            energy_curve=energy,
            emotional_transition="cut_on_beat" if pacing_hint == "FAST" else "soft",
        )
