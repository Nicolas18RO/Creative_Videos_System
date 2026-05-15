"""Tests de validación de subidas del workspace editorial (Fase 6.7)."""

from __future__ import annotations

import pytest

from aicos.application.editorial_training.editorial_training_upload_service import EditorialTrainingUploadService
from aicos.config import EditorialTrainingWorkspaceConfig


@pytest.fixture
def upload_svc(tmp_path) -> EditorialTrainingUploadService:
    cfg = EditorialTrainingWorkspaceConfig(
        enabled=True,
        max_upload_mb=1,
        allowed_video_extensions=[".mp4"],
        allowed_audio_extensions=[".wav"],
    )
    return EditorialTrainingUploadService(workspace_cfg=cfg, uploads_root=tmp_path, media_probe=None)


def test_upload_rejects_unknown_video_extension(upload_svc: EditorialTrainingUploadService) -> None:
    with pytest.raises(ValueError, match="extension"):
        upload_svc.save_video("session-aa", "clip.mov", b"fake-bytes")


def test_upload_accepts_mp4(upload_svc: EditorialTrainingUploadService) -> None:
    out = upload_svc.save_video("session-aa", "clip.mp4", b"x")
    assert out.size_bytes == 1
    assert out.absolute_path.endswith(".mp4")


def test_upload_rejects_oversized(upload_svc: EditorialTrainingUploadService) -> None:
    big = b"x" * (2 * 1024 * 1024)
    with pytest.raises(ValueError, match="too_large"):
        upload_svc.save_video("session-bb", "huge.mp4", big)
