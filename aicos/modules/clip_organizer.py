"""M4: clasificación por visión, naming y colocación en la biblioteca."""

from __future__ import annotations

import logging
import tempfile
import uuid
from pathlib import Path

from sqlalchemy.orm import Session

from aicos.application.clip_organization.classification_adapter import (
    current_taxonomy_from_source_name,
    decision_from_inbound,
    incoming_signal_from_classification,
    vision_classification_from_decision,
)
from aicos.application.clip_organization.organization_execution_service import execute_organization
from aicos.application.clip_organization.organization_preview_service import preview_organization
from aicos.application.clip_organization.organization_sync_service import sync_organized_clip
from aicos.config import get_config
from aicos.core.embedder import Embedder
from aicos.core.vector_store import VectorStore
from aicos.domain.clip_organization.entities import (
    IncomingOrganizationSignal,
    LibraryTaxonomy,
    OrganizationDecision,
    OrganizationResult,
)
from aicos.models.schemas import OrganizeAPIResponse, VisionClassification
from aicos.services import vision_service
from aicos.services.ffmpeg_service import FFmpegService
from aicos.services.llm_service import LLMService
from aicos.taxonomy.parser import parse_filename
from aicos.taxonomy.text_builder import build_semantic_text

logger = logging.getLogger(__name__)


def _response_from_result(
    classification: VisionClassification,
    threshold: float,
    result: OrganizationResult,
    *,
    applied: bool,
    indexed: bool = False,
    risk: str | None = None,
    message: str | None = None,
    clip_id: str | None = None,
) -> OrganizeAPIResponse:
    return OrganizeAPIResponse(
        classification=classification,
        confidence_threshold=threshold,
        applied=applied,
        destination_path=result.destination_path,
        proposed_filename=result.proposal.proposed_filename or None,
        risk=risk or result.risk,
        action=result.proposal.action,
        source_path=result.source_path,
        eligible=result.proposal.eligible,
        clip_id=clip_id or result.proposal.clip_id,
        indexed=indexed,
        message=message or result.message,
    )


def _decision_bundle(
    path: Path,
    *,
    inbound_signal: IncomingOrganizationSignal | None,
    classification: VisionClassification | None,
    source: str,
) -> tuple[VisionClassification, OrganizationDecision, LibraryTaxonomy | None, bool]:
    current = current_taxonomy_from_source_name(path.name)
    if inbound_signal is not None:
        decision = decision_from_inbound(inbound_signal)
        return vision_classification_from_decision(decision), decision, current, True
    if classification is None:
        raise ValueError("Se requiere clasificación o decisión inbound")
    decision = decision_from_inbound(
        incoming_signal_from_classification(
            classification,
            source_name=path.name,
            source=source,
        )
    )
    return classification, decision, current, False


async def organize_clip(
    video_path: Path,
    *,
    apply: bool = False,
    session: Session | None = None,
    library_root: Path | None = None,
    clip_id: str | None = None,
    inbound_signal: IncomingOrganizationSignal | None = None,
) -> OrganizeAPIResponse:
    """Clasifica (o consume una decisión inbound) y opcionalmente mueve + indexa el clip."""
    path = video_path.resolve()
    if not path.is_file():
        raise FileNotFoundError(str(path))

    cfg = get_config()
    threshold = cfg.vision.classification_confidence_threshold
    library_root = library_root or cfg.resolved_paths()["library_root"]
    ffmpeg = FFmpegService()

    derived: VisionClassification | None = None
    derived_source = "filename"
    if inbound_signal is None:
        if cfg.runtime.local_only:
            derived = vision_service.classify_from_path_heuristic(path)
            derived_source = "filename"
        else:
            tmp = Path(tempfile.gettempdir()) / f"aicos_organize_{uuid.uuid4().hex}.jpg"
            try:
                if not ffmpeg.is_available():
                    raise RuntimeError("ffmpeg/ffprobe no disponibles en PATH")
                if not ffmpeg.extract_thumbnail(path, tmp, width=960, height=540, position=0.5):
                    raise RuntimeError("No se pudo extraer frame para visión")
                llm = LLMService()
                derived = await vision_service.classify_frame(tmp, llm)
            finally:
                tmp.unlink(missing_ok=True)
            derived_source = "vision"

    classification, decision, current, approved_inbound = _decision_bundle(
        path,
        inbound_signal=inbound_signal,
        classification=derived,
        source=derived_source,
    )

    if not apply:
        preview = preview_organization(
            source_path=path,
            library_root=library_root,
            decision=decision,
            current_taxonomy=current,
            clip_id=clip_id,
        )
        return _response_from_result(classification, threshold, preview, applied=False, clip_id=clip_id)

    if session is None:
        raise ValueError("Se requiere sesión SQLAlchemy cuando apply=True")

    if not approved_inbound and classification.confidence < threshold:
        return OrganizeAPIResponse(
            classification=classification,
            confidence_threshold=threshold,
            applied=False,
            destination_path=None,
            indexed=False,
            message="Confianza por debajo del umbral; revisar manualmente (M4 needs_review).",
        )
    execution = execute_organization(
        source_path=path,
        library_root=library_root,
        decision=decision,
        current_taxonomy=current,
        clip_id=clip_id,
    )
    if not execution.applied or not execution.destination_path:
        return _response_from_result(classification, threshold, execution, applied=False, clip_id=clip_id)

    dest = Path(execution.destination_path)
    if not dest.is_file():
        return _response_from_result(
            classification,
            threshold,
            execution,
            applied=False,
            risk="INVALID",
            clip_id=clip_id,
            message="Move no verificado: no se actualiza SQLite.",
        )

    tax = parse_filename(dest.name)
    sem = build_semantic_text(tax, dest.name)
    meta_ff = ffmpeg.get_video_metadata(dest)
    file_hash = ffmpeg.compute_file_hash(dest)
    rel = str(dest.resolve().relative_to(Path(library_root).resolve())).replace("\\", "/")

    thumbs = cfg.resolved_paths()["thumbnails_cache"]
    thumbs.mkdir(parents=True, exist_ok=True)
    thumb_path = thumbs / f"{file_hash}_thumb.jpg"
    thumb_ok = ffmpeg.extract_thumbnail(dest, thumb_path, width=cfg.ui.thumbnail_size[0], height=cfg.ui.thumbnail_size[1])

    sync = sync_organized_clip(
        session,
        destination_path=dest,
        library_root=Path(library_root),
        source_path=Path(execution.source_path),
        clip_id=clip_id or execution.proposal.clip_id,
        file_hash=file_hash,
        duration_ms=meta_ff.duration_ms or None,
        resolution_width=meta_ff.width,
        resolution_height=meta_ff.height,
        file_size_bytes=meta_ff.file_size_bytes,
        thumbnail_path=str(thumb_path) if thumb_ok else None,
        semantic_text=sem,
    )
    if not sync.synced or not sync.clip_id:
        return _response_from_result(
            classification,
            threshold,
            execution,
            applied=True,
            clip_id=sync.clip_id or clip_id,
            message=f"{execution.message} {sync.message}",
        )
    clip_id = sync.clip_id

    indexed = False
    try:
        embedder = Embedder()
        store = VectorStore()
        vec = embedder.embed(sem)
        store.upsert_clips(
            ids=[clip_id],
            embeddings=[vec],
            documents=[sem],
            metadatas=[
                {
                    "gender": tax.gender or "",
                    "narrative_function": tax.narrative_function or "",
                    "subcategory": tax.subcategory or "",
                    "context": tax.context or "",
                    "absolute_path": str(dest),
                    "relative_path": rel,
                    "semantic_text": sem[:2000],
                    "naming_compliant": "1" if tax.is_naming_compliant else "0",
                    "variants_in_subcategory": "0",
                    "thumbnail_path": str(thumb_path) if thumb_ok else "",
                }
            ],
        )
        indexed = True
    except RuntimeError as e:
        logger.warning("Índice vectorial omitido: %s", e)

    return _response_from_result(
        classification,
        threshold,
        execution,
        applied=True,
        indexed=indexed,
        risk="NONE",
        clip_id=clip_id,
        message=execution.message,
    )
