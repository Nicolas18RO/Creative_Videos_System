"""Clasificación narrativa por reglas léxicas (es/en), determinística y local."""

from __future__ import annotations

import re
from dataclasses import dataclass

from aicos.domain.cinematic.entities import NarrativeClassificationResult
from aicos.domain.cinematic.enums import NarrativeRole


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").lower()).strip()


# (role, patterns, visual_styles, pacing)
_RULES: list[tuple[NarrativeRole, tuple[str, ...], tuple[str, ...], str]] = [
    (
        NarrativeRole.CTA,
        (
            "compra ya",
            "haz clic",
            "link en bio",
            "link en la bio",
            "descarga",
            "registrate",
            "regístrate",
            "buy now",
            "click here",
            "shop now",
            "limited time",
        ),
        ("direct_address", "bold_typography", "product_hero"),
        "FAST",
    ),
    (
        NarrativeRole.HOOK,
        (
            "imagina",
            "¿y si",
            "stop scrolling",
            "para de scrollear",
            "no vas a creer",
            "esto cambia",
            "atención",
            "wait until",
        ),
        ("pattern_interrupt", "face_cam", "dynamic_motion"),
        "FAST",
    ),
    (
        NarrativeRole.PROBLEM,
        (
            "problema",
            "frustrado",
            "cansado de",
            "tired of",
            "struggle",
            "duele",
            "no funciona",
        ),
        ("relatable_b_roll", "medium_shot", "muted_grade"),
        "MEDIUM",
    ),
    (
        NarrativeRole.AGITATION,
        (
            "empeora",
            "peor",
            "urgente",
            "antes es tarde",
            "you're losing",
            "every day",
            "cada día",
        ),
        ("tight_frames", "quick_cuts", "contrast_lighting"),
        "FAST",
    ),
    (
        NarrativeRole.SOLUTION,
        (
            "solución",
            "solution",
            "finalmente",
            "finally",
            "descubre cómo",
            "here's how",
        ),
        ("product_demo", "clean_background", "step_by_step"),
        "MEDIUM",
    ),
    (
        NarrativeRole.BENEFIT,
        (
            "beneficio",
            "benefits",
            "ahorra",
            "save time",
            "más fácil",
            "easier",
            "resultados",
        ),
        ("split_screen", "text_callouts", "bright_grade"),
        "MEDIUM",
    ),
    (
        NarrativeRole.SOCIAL_PROOF,
        (
            "reseñas",
            "reviews",
            "5 estrellas",
            "trusted by",
            "miles de",
            "thousands of",
            "clientes",
            "customers",
        ),
        ("ugc_montage", "logo_strip", "talking_head"),
        "MEDIUM",
    ),
    (
        NarrativeRole.TESTIMONIAL,
        (
            "testimonio",
            "testimonial",
            "yo usé",
            "i used",
            "mi experiencia",
            "my experience",
        ),
        ("talking_head", "authentic_location", "natural_light"),
        "SLOW",
    ),
    (
        NarrativeRole.DEMONSTRATION,
        (
            "mira cómo",
            "watch how",
            "tutorial",
            "paso a paso",
            "step by step",
            "demo",
        ),
        ("screen_recording", "over_shoulder", "macro_product"),
        "MEDIUM",
    ),
    (
        NarrativeRole.EDUCATIONAL,
        (
            "dato",
            "fact",
            "estudio",
            "study",
            "tip",
            "consejo",
            "aprende",
            "learn",
        ),
        ("graphics", "b_roll", "lower_thirds"),
        "SLOW",
    ),
    (
        NarrativeRole.STORYTELLING,
        (
            "había una vez",
            "once upon",
            "años atrás",
            "years ago",
            "historia",
            "story",
        ),
        ("establishing_shot", "warm_light", "slow_push"),
        "SLOW",
    ),
    (
        NarrativeRole.BEFORE_AFTER,
        (
            "antes y después",
            "before and after",
            "antes / después",
            "then vs now",
        ),
        ("split_screen", "wipe_transition", "side_by_side"),
        "MEDIUM",
    ),
    (
        NarrativeRole.CURIOSITY_LOOP,
        (
            "pero espera",
            "but wait",
            "aún no",
            "not yet",
            "spoiler",
        ),
        ("reveal_shot", "match_cut", "punch_in"),
        "FAST",
    ),
    (
        NarrativeRole.EMOTIONAL_PEAK,
        (
            "lo logré",
            "i made it",
            "gracias",
            "thank you",
            "nunca olvidaré",
            "dream come true",
        ),
        ("close_up", "tear_jerker_light", "shallow_dof"),
        "SLOW",
    ),
    (
        NarrativeRole.TRANSITION,
        (
            "siguiente",
            "next",
            "pasemos a",
            "let's move",
            "ahora",
            "now",
        ),
        ("whip_pan", "flash_frame", "graphic_transition"),
        "FAST",
    ),
]


@dataclass(slots=True)
class RuleBasedNarrativeProvider:
    """Proveedor local sin modelo neuronal."""

    @property
    def provider_id(self) -> str:
        return "rules"

    def classify(
        self,
        transcript: str,
        scene_text: str,
        context: str | None = None,
    ) -> NarrativeClassificationResult | None:
        blob = _norm(f"{transcript} {scene_text} {context or ''}")
        if not blob:
            return NarrativeClassificationResult(
                narrative_role=NarrativeRole.UNKNOWN,
                confidence=0.2,
                reasoning="Texto vacío; rol desconocido.",
                compatible_visual_styles=("neutral_b_roll",),
                pacing_recommendation="MEDIUM",
            )
        best: tuple[NarrativeRole, float, str, tuple[str, ...], str] | None = None
        for role, patterns, styles, pacing in _RULES:
            hits = sum(1 for p in patterns if p in blob)
            if hits == 0:
                continue
            conf = min(0.95, 0.45 + 0.12 * hits)
            reason = f"Coincidencia léxica ({hits}) con patrones de rol {role.value}."
            cand = (role, conf, reason, styles, pacing)
            if best is None or conf > best[1]:
                best = cand
        if best is None:
            if len(blob) < 24:
                return NarrativeClassificationResult(
                    narrative_role=NarrativeRole.TRANSITION,
                    confidence=0.35,
                    reasoning="Texto muy corto; se asume transición o filler.",
                    compatible_visual_styles=("b_roll",),
                    pacing_recommendation="FAST",
                )
            return NarrativeClassificationResult(
                narrative_role=NarrativeRole.STORYTELLING,
                confidence=0.3,
                reasoning="Sin patrones fuertes; storytelling genérico por defecto.",
                compatible_visual_styles=("b_roll", "talking_head"),
                pacing_recommendation="MEDIUM",
            )
        role, conf, reason, styles, pacing = best
        return NarrativeClassificationResult(
            narrative_role=role,
            confidence=conf,
            reasoning=reason,
            compatible_visual_styles=styles,
            pacing_recommendation=pacing,
        )
