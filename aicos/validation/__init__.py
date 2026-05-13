"""Validación de sistema (health checks, solo lectura)."""

__all__ = ["run_system_validation"]


def __getattr__(name: str):
    if name == "run_system_validation":
        from aicos.validation.system_validation import run_system_validation

        return run_system_validation
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
