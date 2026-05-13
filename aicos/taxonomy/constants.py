"""Mapas de expansión semántica y subcategorías reconocidas en filenames."""

from __future__ import annotations

NARRATIVE_FUNCTIONS: frozenset[str] = frozenset(
    {
        "HOOK",
        "PROBLEM",
        "BENEFIT",
        "RESULT",
        "AUTHORITY",
        "SOCIAL_PROOF",
        "NATURAL",
        "CTA",
    }
)

GENDER_PREFIXES: frozenset[str] = frozenset({"F", "M", "N", "MIX", "KIDS", "NEUTRAL", "KID"})

# Prefijos legacy → normalizado (aplicado al primer token del stem)
LEGACY_GENDER_PREFIXES: dict[str, str] = {"NEUTRAL": "N", "KID": "KIDS"}

NARRATIVE_EXPANSIONS: dict[str, str] = {
    "HOOK": (
        "hook attention grabbing opening shocking reveal problem teaser first seconds "
        "grab engagement"
    ),
    "PROBLEM": (
        "problem pain symptom suffering complaint issue difficulty struggle hurt ache "
        "discomfort"
    ),
    "BENEFIT": (
        "benefit daily life activity normal routine improvement solution using product "
        "comfortable living"
    ),
    "RESULT": (
        "result recovery improvement transformation success healing after before better "
        "progress"
    ),
    "AUTHORITY": (
        "authority credibility trust doctor medical laboratory science animation proof "
        "clinical expert"
    ),
    "SOCIAL_PROOF": (
        "testimonial social proof review satisfied customer real person experience selfie "
        "talking camera"
    ),
    "NATURAL": (
        "natural ingredient herb botanical extract source raw organic plant traditional "
        "wellness"
    ),
    "CTA": "call to action buy purchase order now limited offer package shipping",
}

GENDER_SEMANTIC: dict[str, str] = {
    "F": "woman female adult protagonist",
    "M": "man male adult protagonist",
    "N": "neutral object no person animation scientific b-roll product",
    "MIX": "couple mixed group people together family",
    "KIDS": "child kid young boy girl children",
}

# Subcategorías usadas para prefijo más largo en parser (no exhaustivo de toda la biblioteca;
# se amplía con heurística de último token = contexto).
KNOWN_SUBCATEGORIES: frozenset[str] = frozenset(
    {
        # Comunes salud / hooks / problem
        "KNEE_PAIN",
        "KNEE_PROBLEM",
        "BACK_PAIN",
        "NECK_PAIN",
        "HIP_PAIN",
        "SHOULDER_PAIN",
        "HAND_PROBLEM",
        "HAND_PAIN",
        "FEET_PAIN",
        "STOMACH_PAIN",
        "CRAMP_PAIN",
        "WALK_PAIN",
        "URINARY_INCONTINENCE",
        "WEIGHT_PROBLEM",
        "EYE_PROBLEM",
        "VISION_PROBLEM",
        "SLEEPING_PROBLEM",
        "STRESS_OVERWHELM",
        "SKIN_PROBLEM",
        "CELLULITIS",
        "BAD_SMELL",
        "PUSSY",
        "DISAGREEMENT",
        "DRINKING",
        "HEAD_PROBLEM",
        "SEXUAL_PHYSICAL",
        "SOCIAL_CONFIDENCE",
        "IDEAL_PHYSICAL_STATE",
        "IDEAL_SKIN",
        "IDEAL_PHYSICAL",
        "CLEANING",
        "DAILY_ROUTINE",
        "BODY",
        "HAIR_PROBLEM",
        "PAIN_BACK",
        "ANIMATION",
        "ANIMATION_3D",
        "KNEE_ANIMATION",
        "EYE_ANIMATION",
        "NEURON_ANIMATION",
        "CELL_ANIMATION",
        "BODY_PROBLEM",
        "VEHICLE_PROBLEM",
        "ENGINE",
        "SMOKE",
        "SURGERY",
        "ANATOMY",
        "BEVERAGE",
        "FAT",
        "MICROBIO",
        "PENIS",
        "TESTIMONIAL_SELFIE",
        "CHIROPRACTOR_TALKING",
        "RAW_INGREDIENT",
        "INGREDIENT_SOURCE",
        "LABORATORY",
        "SURGERY_HOSPITAL",
        "VEHICLE",
        "SKIN_RECOVERY",
        "IDEAL_PHYSICAL_STATE",
        "PHYSICAL_TRANSFORMATION",
        "WALKING_RECOVERY",
        "SOLUTION_FOUND",
        "PHYSICAL_PROGRESS",
        "TRANQUILLITY",
        "SEXUAL_STATE",
        "EXERCISING_PROCESS",
        "HAIR_RECOVERY",
        "SANITARY_TOWEL",
        "WORKING_COMPUTER",
        "BUY_NOW",
        "DEVELOPMENT",
        "PLAYING",
        "COUPLE",
        "CONTEX",
        "SLEEPING",
        "OLDMAN",
        "OLDWOMAN",
        "BEFORE_AFTER",
        "WRINKLES",
        "BLUE_LIGHT",
        "DRIVING",
        "INFLAMMATION",
        "POSTURE",
        "INJECTION",
        "TAKING_PHILLS",
        "TAKING_PILLS",
        "PHILL_VISUAL",
        "FORMULATION_PROCESS",
        "NATURAL_EXTRACT",
    }
)

SUBCATEGORY_EXPANSIONS: dict[str, str] = {
    "KNEE_PAIN": (
        "knee joint articular cartilage pain ache hurt walk stairs climbing rodilla "
        "articulación"
    ),
    "KNEE_PROBLEM": "knee joint mobility pain injury articulation",
    "BACK_PAIN": (
        "back spine lumbar pain ache posture herniated disc espalda columna lumbar strain"
    ),
    "URINARY_INCONTINENCE": (
        "bladder urinary leakage incontinence pelvic floor sneeze laugh jump vejiga pérdida"
    ),
    "WEIGHT_PROBLEM": "overweight obesity fat body weight loss diet adelgazar sobrepeso",
    "SLEEPING_PROBLEM": "insomnia sleep disorder fatigue tired rest insomnio dormir",
    "EYE_PROBLEM": "vision eye sight blur driving computer screen fatigue ojo visión",
    "HAIR_PROBLEM": "hair loss thinning bald scalp irritation cabello caída calvicie",
    "STRESS_OVERWHELM": "stress anxiety overwhelm worry mental burnout estrés ansiedad",
    "SKIN_PROBLEM": "skin wrinkles dry aging spots collagen piel arrugas",
    "DAILY_ROUTINE": "daily life activity routine normal lifestyle actividad cotidiana",
    "ANIMATION": "3d animation medical scientific visualization anatomy organ cellular",
    "KNEE_ANIMATION": "knee 3d medical visualization joint cartilage recovery animation",
    "EYE_ANIMATION": "eye vision medical animation surgery ocular",
    "NEURON_ANIMATION": "neuron nerve brain cell signal neurology",
    "CELL_ANIMATION": "cell microscopic dna biology medical",
    "BODY_PROBLEM": "body health symptom medical condition",
    "VEHICLE_PROBLEM": "car engine smoke vehicle automotive failure",
    "NATURAL": "natural wellness botanical ingredient",
    "RAW_INGREDIENT": "raw natural ingredient supplement extract",
    "INGREDIENT_SOURCE": "source harvest farm botanical ingredient origin",
    "STAIRS": "stairs steps climbing going up effort mobility",
    "WALK_PAIN": "walking pain mobility gait difficulty",
}

CONTEXT_EXPANSIONS: dict[str, str] = {
    "STAIRS": "stairs steps climbing going up down effort",
    "POSTURE": "posture sitting standing alignment ergonomic",
    "IA": "ai generated synthetic computer graphics",
    "OLDMAN": "older male senior mature man",
    "OLDWOMAN": "older female senior mature woman",
    "BEFORE_AFTER": "before after transformation comparison",
    "DRIVING": "driving car road steering commute",
    "INFLAMMATION": "inflammation swelling redness pain acute",
}

DOMAIN_TRANSLATION_MAP: dict[str, str] = {
    "dolor de rodilla": "knee pain",
    "dolor rodilla": "knee pain",
    "rodilla": "knee pain",
    "escaleras": "stairs climbing",
    "dolor de espalda": "back pain",
    "incontinencia urinaria": "urinary incontinence",
    "caída del cabello": "hair loss",
    "visión borrosa": "blurry vision",
    "subir escaleras": "going up stairs",
    "bajar escaleras": "going down stairs",
    "pérdida de peso": "weight loss",
    "natural": "natural wellness",
}
