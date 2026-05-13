"""POST /organize — M4 clasificación y archivo en biblioteca."""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException

from aicos.database.db import session_scope
from aicos.models.schemas import OrganizeAPIResponse, OrganizeRequestBody
from aicos.modules.clip_organizer import organize_clip

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=OrganizeAPIResponse)
async def organize(body: OrganizeRequestBody) -> OrganizeAPIResponse:
    """Clasifica un video local; con `apply=true` lo mueve a la biblioteca e indexa."""
    p = Path(body.video_path).expanduser().resolve()
    if not p.is_file():
        raise HTTPException(status_code=400, detail=f"Archivo no encontrado: {p}")
    try:
        if body.apply:
            with session_scope() as session:
                return await organize_clip(p, apply=True, session=session)
        return await organize_clip(p, apply=False, session=None)
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.exception("Fallo en organize")
        raise HTTPException(status_code=500, detail=str(e)) from e
