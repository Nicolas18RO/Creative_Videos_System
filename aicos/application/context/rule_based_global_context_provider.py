"""Analizador de contexto global por reglas léxicas (offline, sin APIs externas)."""

from __future__ import annotations

import logging
import re
import time
from dataclasses import replace

from aicos.domain.context.entities import GlobalContext, GlobalContextValidation
from aicos.domain.context.enums import ContextIntent, IndustryType, NarrativeArc, VisualStyle

logger = logging.getLogger(__name__)

_INDUSTRY_LEXICON: list[tuple[IndustryType, tuple[str, ...], float]] = [
    (
        IndustryType.AUTOMOTIVE,
        (
            "motor",
            "motores",
            "aceite",
            "oil",
            "humo",
            "smoke",
            "coche",
            "carro",
            "auto",
            "car ",
            "vehículo",
            "vehicle",
            "pistón",
            "piston",
            "cilindro",
            "cylinder",
            "aditivo",
            "additive",
            "taller",
            "mecánico",
            "mechanical",
            "transmisión",
            "transmission",
            "radiador",
            "radiator",
            "block",
            "bloque",
            "engine",
        ),
        1.0,
    ),
    (
        IndustryType.COSMETICS,
        (
            "piel",
            "skin",
            "crema",
            "cream",
            "serum",
            "maquillaje",
            "makeup",
            "antiarrugas",
            "wrinkle",
            "rutina facial",
            "skincare",
            "labial",
            "pestañas",
        ),
        1.0,
    ),
    (
        IndustryType.MEDICAL,
        (
            "doctor",
            "dosis",
            "síntoma",
            "symptom",
            "paciente",
            "patient",
            "clínica",
            "clinic",
            "medicamento",
            "diagnóstico",
            "diagnosis",
            "salud",
            "health",
        ),
        1.0,
    ),
    (
        IndustryType.FITNESS,
        (
            "gym",
            "músculo",
            "muscle",
            "entrenamiento",
            "workout",
            "proteína",
            "protein",
            "cardio",
        ),
        0.95,
    ),
    (
        IndustryType.TECH,
        (
            "software",
            "app",
            "código",
            "code",
            "cloud",
            "saas",
            "api",
            "datos",
            "data",
        ),
        0.9,
    ),
    (
        IndustryType.FINANCE,
        (
            "inversión",
            "investment",
            "crédito",
            "credit",
            "hipoteca",
            "mortgage",
            "ahorro",
            "saving",
        ),
        0.9,
    ),
    (
        IndustryType.FOOD,
        (
            "receta",
            "recipe",
            "sabor",
            "flavor",
            "cocina",
            "kitchen",
            "nutrición",
            "nutrition",
        ),
        0.85,
    ),
    (
        IndustryType.HOME,
        (
            "hogar",
            "home",
            "limpieza",
            "cleaning",
            "decoración",
            "furniture",
            "mueble",
        ),
        0.85,
    ),
    (
        IndustryType.EDUCATION,
        (
            "curso",
            "course",
            "aprender",
            "learn",
            "clase",
            "class",
            "estudio",
            "study",
        ),
        0.85,
    ),
]

_CONCERN_MARKERS = (
    "daño",
    "damage",
    "destru",
    "destroy",
    "humo",
    "smoke",
    "falla",
    "failure",
    "peligro",
    "danger",
    "riesgo",
    "risk",
    "alerta",
    "warning",
    "preocup",
    "worry",
)

_SOLUTION_MARKERS = (
    "solución",
    "solution",
    "arregla",
    "fix",
    "protege",
    "protect",
    "previene",
    "prevent",
    "mejora",
    "improve",
    "ahorra",
    "save",
)

_PROBLEM_MARKERS = (
    "problema",
    "problem",
    "duele",
    "hurt",
    "frustr",
    "struggle",
    "error",
    "mal",
    "bad",
)

_STOP = frozenset(
    "el la los las un una unos unas y o de del al por para con sin sobre entre que como cuando "
    "si ya muy más menos todo esta este estos es son fue ser tu su sus nos les me te se lo le da "
    "hay sea the and for with this that are was is been being".split()
)


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def _tokens(text: str) -> list[str]:
    raw = re.sub(r"[^\w\sáéíóúñü]", " ", _norm(text), flags=re.UNICODE)
    return [t for t in raw.split() if len(t) >= 3 and t not in _STOP]


class RuleBasedGlobalContextProvider:
    """Implementa extracción local; compatible con ``ContextAnalyzerPort``."""

    def analyze(
        self,
        transcript_text: str,
        *,
        product_category: str | None,
        target_audience: str | None,
    ) -> GlobalContext:
        t0 = time.perf_counter()
        blob = _norm(transcript_text)
        flags: set[str] = set()
        if not blob:
            flags.add("empty_transcript")
            ctx = self._fallback("", flags, "Transcripción vacía.")
            logger.info("[GlobalContext] flags=%s elapsed_ms=%.1f", sorted(flags), (time.perf_counter() - t0) * 1000)
            return ctx
        if len(blob) < 40:
            flags.add("transcript_too_short")
        if len(set(_tokens(transcript_text))) < 4:
            flags.add("low_signal_irrelevant")

        scores: dict[IndustryType, float] = {}
        for ind, patterns, weight in _INDUSTRY_LEXICON:
            hits = sum(1 for p in patterns if p in blob)
            if hits:
                scores[ind] = scores.get(ind, 0.0) + weight * min(hits, 6)

        # Pistas de request body (no dominan pero sesgan)
        if product_category:
            pc = _norm(product_category)
            if any(x in pc for x in ("auto", "motor", "veh")):
                scores[IndustryType.AUTOMOTIVE] = scores.get(IndustryType.AUTOMOTIVE, 0.0) + 0.6
            if any(x in pc for x in ("cosmetic", "belleza", "skin")):
                scores[IndustryType.COSMETICS] = scores.get(IndustryType.COSMETICS, 0.0) + 0.6
            if any(x in pc for x in ("salud", "health", "med")):
                scores[IndustryType.MEDICAL] = scores.get(IndustryType.MEDICAL, 0.0) + 0.5

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        if not ranked:
            flags.add("entities_absent")
            industry = IndustryType.GENERAL
            topic = "general content"
        else:
            industry = ranked[0][0]
            if len(ranked) > 1 and ranked[1][1] > 0 and ranked[0][1] / max(ranked[1][1], 0.01) < 1.25:
                flags.add("ambiguous_industry")
            if len(ranked) > 1 and ranked[1][1] >= ranked[0][1] * 0.85:
                flags.add("multiple_industries_detected")

            topic = self._topic_from_industry(industry, blob)

        secondary = tuple(r[0] for r in ranked[1:3] if r[1] >= ranked[0][1] * 0.55) if ranked else ()

        anchors = self._build_anchors(blob, industry)
        entities = tuple(sorted(set(anchors) | set(self._entities_from_lexicon(blob, industry))))[:24]
        if not anchors:
            flags.add("entities_absent")

        dominant_emotion = self._dominant_emotion(blob)
        narrative_arc = self._infer_arc(blob)
        visual_style = self._visual_style(industry, blob)
        content_intent = self._intent(blob)
        product_context = self._product_context(industry, blob, product_category)
        cinematic_context = self._cinematic_context(industry, visual_style)
        continuity_context = (
            f"Cohesive narrative about {topic} within {industry.value} vertical; "
            f"audience {target_audience or 'general'}."
        )

        notes = ""
        if "ambiguous_industry" in flags:
            notes = "Varias industrias con puntuación cercana; se priorizó la de mayor peso léxico."

        ctx = GlobalContext(
            id="",
            project_id=None,
            topic=topic,
            industry=industry,
            semantic_entities=entities,
            dominant_emotion=dominant_emotion,
            narrative_arc=narrative_arc,
            visual_style=visual_style,
            semantic_anchors=tuple(anchors[:20]),
            content_intent=content_intent,
            cinematic_context=cinematic_context,
            product_context=product_context,
            continuity_context=continuity_context,
            validation=GlobalContextValidation(flags=frozenset(flags), notes=notes),
            secondary_industries=secondary,
            embedding_vector_id=None,
            transcript_fingerprint="",
        )
        logger.info(
            "[ContextInference] topic=%s industry=%s emotion=%s arc=%s anchors=%d elapsed_ms=%.1f",
            topic,
            industry.value,
            dominant_emotion,
            narrative_arc.value,
            len(anchors),
            (time.perf_counter() - t0) * 1000,
        )
        logger.info("[SemanticAnchors] anchors=%s", list(ctx.semantic_anchors)[:12])
        logger.info("[NarrativeArc] arc=%s flags=%s", narrative_arc.value, sorted(flags))
        return ctx

    def _fallback(self, blob: str, flags: set[str], notes: str) -> GlobalContext:
        return GlobalContext(
            id="",
            project_id=None,
            topic="unknown",
            industry=IndustryType.GENERAL,
            semantic_entities=(),
            dominant_emotion="neutral",
            narrative_arc=NarrativeArc.UNKNOWN,
            visual_style=VisualStyle.UNKNOWN,
            semantic_anchors=(),
            content_intent=ContextIntent.UNKNOWN,
            cinematic_context="unknown visual context",
            product_context="unspecified product",
            continuity_context="insufficient transcript signal",
            validation=GlobalContextValidation(flags=frozenset(flags), notes=notes),
            secondary_industries=(),
            embedding_vector_id=None,
            transcript_fingerprint="",
        )

    def _topic_from_industry(self, industry: IndustryType, blob: str) -> str:
        if industry == IndustryType.AUTOMOTIVE:
            if "additive" in blob or "aditivo" in blob:
                return "engine additive performance"
            if "smoke" in blob or "humo" in blob:
                return "engine smoke mechanical stress"
            return "automotive maintenance"
        if industry == IndustryType.COSMETICS:
            return "skin beauty routine"
        if industry == IndustryType.MEDICAL:
            return "health medical guidance"
        mapping = {
            IndustryType.FITNESS: "fitness training",
            IndustryType.TECH: "technology product",
            IndustryType.FINANCE: "personal finance",
            IndustryType.FOOD: "food nutrition",
            IndustryType.HOME: "home lifestyle",
            IndustryType.EDUCATION: "learning education",
            IndustryType.GENERAL: "general content",
        }
        return mapping.get(industry, "general content")

    def _entities_from_lexicon(self, blob: str, industry: IndustryType) -> list[str]:
        found: list[str] = []
        for ind, patterns, _w in _INDUSTRY_LEXICON:
            if ind != industry:
                continue
            for p in patterns:
                if len(p) >= 3 and p in blob:
                    found.append(p.strip())
        return found

    def _build_anchors(self, blob: str, industry: IndustryType) -> list[str]:
        anchors: list[str] = []
        pairs = (
            ("engine", "smoke"),
            ("motor", "humo"),
            ("oil", "engine"),
            ("aceite", "motor"),
            ("car", "damage"),
            ("coche", "daño"),
        )
        for a, b in pairs:
            if a in blob and b in blob:
                anchors.extend([a, b])
        if industry == IndustryType.AUTOMOTIVE:
            for term in (
                "engine",
                "motor",
                "oil",
                "aceite",
                "smoke",
                "humo",
                "car",
                "coche",
                "mechanical damage",
                "daño mecánico",
                "additive",
                "aditivo",
            ):
                if term.replace(" ", "") in blob.replace(" ", "") or term in blob:
                    anchors.append(term.replace(" ", "_") if " " in term else term)
        toks = _tokens(blob)
        anchors.extend(toks[:10])
        # dedupe preserve order
        seen: set[str] = set()
        out: list[str] = []
        for x in anchors:
            k = x.lower()
            if k not in seen and len(k) >= 2:
                seen.add(k)
                out.append(x.lower())
        return out

    def _dominant_emotion(self, blob: str) -> str:
        if any(m in blob for m in _CONCERN_MARKERS):
            return "concern"
        if any(m in blob for m in ("excited", "emocion", "increíble", "amazing", "wow")):
            return "excitement"
        if any(m in blob for m in ("confianza", "trust", "garant", "guarantee")):
            return "trust"
        return "neutral"

    def _infer_arc(self, blob: str) -> NarrativeArc:
        has_prob = any(m in blob for m in _PROBLEM_MARKERS)
        has_sol = any(m in blob for m in _SOLUTION_MARKERS)
        if has_prob and has_sol:
            return NarrativeArc.PROBLEM_SOLUTION
        if any(m in blob for m in ("testimon", "review", "cliente satisfecho")):
            return NarrativeArc.TESTIMONIAL
        if any(m in blob for m in ("aprende", "learn", "tip", "dato", "cómo funciona")):
            return NarrativeArc.EDUCATIONAL
        if any(m in blob for m in ("oferta", "compra", "discount", "buy now")):
            return NarrativeArc.PROMOTIONAL
        if has_prob or has_sol:
            return NarrativeArc.AWARENESS_CONSIDERATION
        return NarrativeArc.UNKNOWN

    def _visual_style(self, industry: IndustryType, blob: str) -> VisualStyle:
        if industry == IndustryType.AUTOMOTIVE:
            return VisualStyle.MECHANICAL_CINEMATIC
        if industry == IndustryType.COSMETICS:
            return VisualStyle.BEAUTY_SOFT_LIGHT
        if industry == IndustryType.MEDICAL:
            return VisualStyle.CLINICAL_CLEAN
        if industry == IndustryType.FITNESS:
            return VisualStyle.UGC_HANDHELD
        if industry == IndustryType.TECH:
            return VisualStyle.TECH_MINIMAL
        if industry == IndustryType.FOOD:
            return VisualStyle.FOOD_APPETITE
        return VisualStyle.LIFESTYLE_WARM

    def _intent(self, blob: str) -> ContextIntent:
        if any(m in blob for m in _CONCERN_MARKERS):
            return ContextIntent.WARN
        if any(m in blob for m in ("compra", "buy", "oferta", "order now")):
            return ContextIntent.PERSUADE
        if any(m in blob for m in ("aprende", "learn", "explícame", "explain")):
            return ContextIntent.EDUCATE
        if any(m in blob for m in ("inspira", "dream", "sueña")):
            return ContextIntent.INSPIRE
        if any(m in blob for m in ("reír", "funny", "meme")):
            return ContextIntent.ENTERTAIN
        return ContextIntent.UNKNOWN

    def _product_context(self, industry: IndustryType, blob: str, product_category: str | None) -> str:
        base = product_category or industry.value
        if industry == IndustryType.AUTOMOTIVE and ("aditivo" in blob or "additive" in blob):
            return f"automotive engine additive ({base})"
        return f"{industry.value} offer ({base})"

    def _cinematic_context(self, industry: IndustryType, style: VisualStyle) -> str:
        return f"{style.value} framing for {industry.value} storytelling"


class RuleBasedNarrativeInferenceProvider:
    """Refuerzo de arco narrativo con reglas adicionales (mismo paquete offline)."""

    def infer_arc(self, transcript_text: str, current: GlobalContext) -> GlobalContext:
        blob = _norm(transcript_text)
        arc = current.narrative_arc
        if "antes" in blob and ("después" in blob or "despues" in blob):
            arc = NarrativeArc.STORY_ARC
        if arc == NarrativeArc.UNKNOWN and len(blob) > 200:
            arc = NarrativeArc.AWARENESS_CONSIDERATION
        logger.info("[NarrativeArc] refine arc=%s", arc.value)
        return replace(current, narrative_arc=arc)
