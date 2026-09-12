"""POST /organize — preview (default) o apply de organización M4."""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from aicos.application.clip_organization.classification_adapter import incoming_signal_from_body
from aicos.database.db import session_scope
from aicos.models.schemas import OrganizeAPIResponse, OrganizeRequestBody
from aicos.modules.clip_organizer import organize_clip
from aicos.services import library_service

logger = logging.getLogger(__name__)
router = APIRouter()


def _resolve_source(body: OrganizeRequestBody) -> tuple[Path, str | None]:
    clip_id = body.resolved_clip_id()
    video_path = body.resolved_video_path()
    if clip_id and not video_path:
        with session_scope() as session:
            row = library_service.get_clip_by_id(session, clip_id)
        if row is None:
            raise HTTPException(status_code=404, detail=f"clip_not_found: {clip_id}")
        video_path = row.absolute_path
    assert video_path is not None
    path = Path(video_path).expanduser().resolve()
    if not path.is_file():
        raise HTTPException(status_code=400, detail=f"Archivo no encontrado: {path}")
    return path, clip_id


@router.post("", response_model=OrganizeAPIResponse)
async def organize(body: OrganizeRequestBody) -> OrganizeAPIResponse | JSONResponse:
    """Dry-run por defecto. `apply=true` mueve solo si la propuesta es elegible."""
    path, clip_id = _resolve_source(body)
    inbound = incoming_signal_from_body(body.decision) if body.decision is not None else None
    try:
        if body.apply:
            with session_scope() as session:
                result = await organize_clip(
                    path,
                    apply=True,
                    session=session,
                    clip_id=clip_id,
                    inbound_signal=inbound,
                )
        else:
            result = await organize_clip(
                path,
                apply=False,
                session=None,
                clip_id=clip_id,
                inbound_signal=inbound,
            )
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Fallo en organize")
        raise HTTPException(status_code=500, detail=str(e)) from e

    if body.apply and result.risk == "COLLISION":
        return JSONResponse(status_code=409, content=jsonable_encoder(result))
    return result
