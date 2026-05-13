"""Extracción de intenciones visuales desde texto (reglas locales)."""

from __future__ import annotations

import re
from dataclasses import dataclass

from aicos.domain.cinematic.entities import VisualIntent
from aicos.domain.cinematic.enums import VisualIntentKind


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").lower()).strip()


@dataclass(slots=True)
class RuleBasedVisualIntentExtractor:
    """Convierte frases de marketing en intents cinematográficos sugeridos."""

    def extract(self, transcript: str, scene_text: str) -> tuple[VisualIntent, ...]:
        blob = _norm(f"{transcript} {scene_text}")
        intents: list[VisualIntent] = []
        if any(
            x in blob
            for x in (
                "termina hoy",
                "ends today",
                "últimas horas",
                "last hours",
                "solo hoy",
                "today only",
            )
        ):
            intents.append(
                VisualIntent(
                    intent_type=VisualIntentKind.URGENCY,
                    cinematic_priority=0.92,
                    suggested_camera_styles=("handheld", "punch_in"),
                    suggested_editing_styles=("quick_cuts", "whoosh_sfx"),
                    suggested_visual_elements=("countdown_ui", "red_banner"),
                    suggested_motion=("whip_pan", "snap_zoom"),
                    suggested_color_mood=("high_contrast", "warm_accent"),
                    suggested_transition_style=("hard_cut",),
                    suggested_shot_types=("close_up", "insert_product"),
                )
            )
        if "countdown" in blob or "cuenta atrás" in blob or "timer" in blob:
            intents.append(
                VisualIntent(
                    intent_type=VisualIntentKind.COUNTDOWN,
                    cinematic_priority=0.88,
                    suggested_camera_styles=("locked_off",),
                    suggested_editing_styles=("motion_graphics",),
                    suggested_visual_elements=("digital_timer", "lower_third"),
                    suggested_motion=("static",),
                    suggested_color_mood=("neon",),
                    suggested_transition_style=("flash",),
                    suggested_shot_types=("insert", "extreme_close_up"),
                )
            )
        if any(x in blob for x in ("oferta", "sale", "discount", "descuento", "% off")):
            intents.append(
                VisualIntent(
                    intent_type=VisualIntentKind.HIGH_ATTENTION,
                    cinematic_priority=0.75,
                    suggested_camera_styles=("gimbal", "tripod_lock"),
                    suggested_editing_styles=("beat_sync",),
                    suggested_visual_elements=("price_tag", "sticker_burst"),
                    suggested_motion=("push_in",),
                    suggested_color_mood=("vibrant",),
                    suggested_transition_style=("zoom_blur",),
                    suggested_shot_types=("medium_close", "product_hero"),
                )
            )
        if any(x in blob for x in ("testimonio", "review", "⭐", "stars", "cliente")):
            intents.append(
                VisualIntent(
                    intent_type=VisualIntentKind.SOCIAL_PROOF_VISUAL,
                    cinematic_priority=0.7,
                    suggested_camera_styles=("ugc_handheld",),
                    suggested_editing_styles=("jump_cut_light",),
                    suggested_visual_elements=("face_cam", "screenshot_overlay"),
                    suggested_motion=("subtle_pan",),
                    suggested_color_mood=("natural",),
                    suggested_transition_style=("j_cut",),
                    suggested_shot_types=("talking_head",),
                )
            )
        if not intents:
            intents.append(
                VisualIntent(
                    intent_type=VisualIntentKind.GENERIC,
                    cinematic_priority=0.4,
                    suggested_camera_styles=("medium",),
                    suggested_editing_styles=("standard",),
                    suggested_visual_elements=("b_roll",),
                    suggested_motion=("slow",),
                    suggested_color_mood=("balanced",),
                    suggested_transition_style=("dissolve",),
                    suggested_shot_types=("wide", "medium"),
                )
            )
        return tuple(intents)
