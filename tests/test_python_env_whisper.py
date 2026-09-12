"""Diagnóstico de import Whisper / tokenizers."""

from aicos.runtime.python_env import format_whisper_import_failure


def test_format_tokenizers_missing_hint():
    exc = ModuleNotFoundError("No module named 'tokenizers'")
    reason, hint = format_whisper_import_failure(exc)
    assert "tokenizers" in reason
    assert "tokenizers" in hint
