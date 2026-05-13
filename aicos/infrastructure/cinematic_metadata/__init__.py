"""Infraestructura: lectores y codificadores para metadatos cinematográficos."""

from aicos.infrastructure.cinematic_metadata.openclip_frame_encoder import OpenClipFrameEncoder
from aicos.infrastructure.cinematic_metadata.sql_clip_metadata_read_adapter import (
    SqlClipCinematicMetadataReadAdapter,
)

__all__ = ["OpenClipFrameEncoder", "SqlClipCinematicMetadataReadAdapter"]
