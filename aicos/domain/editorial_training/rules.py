"""Reglas de validación puras (Fase 6.7)."""


def validate_correction_reward(reward: float) -> float:
    return max(-1.0, min(1.0, float(reward)))
