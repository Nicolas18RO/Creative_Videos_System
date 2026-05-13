"""M4: clasificación por visión, naming y colocación en la biblioteca."""

from __future__ import annotations

import logging
import shutil
import tempfile
import uuid
from pathlib import Path

from sqlalchemy.orm import Session

from aicos.config import get_config
from aicos.core.embedder import Embedder
from aicos.core.vector_store import VectorStore
from aicos.models.schemas import OrganizeAPIResponse, VisionClassification
from aicos.services import library_service, vision_service
from aicos.services.ffmpeg_service import FFmpegService
from aicos.services.llm_service import LLMService
from aicos.taxonomy.parser import parse_filename
from aicos.taxonomy.text_builder import build_semantic_text

logger = logging.getLogger(__name__)


def _normalize_folder(folder: str) -> Path:
    return Path(folder.replace("\\", "/").strip("/"))


def _build_filename(v: VisionClassification, variant: int) -> str:
    parts = [
        v.gender.strip().upper(),
        v.narrative_function.strip().upper(),
        v.subcategory.strip().upper().replace(" ", "_"),
    ]
    ctx = (v.context or "").strip()
    if ctx and ctx.upper() not in ("NULL", "NONE"):
        parts.append(ctx.upper().replace(" ", "_"))
    if v.is_ai_generated:
        parts.append("IA")
    parts.append(f"{variant:02d}")
    return "_".join(parts) + ".mp4"


async def organize_clip(
    video_path: Path,
    *,
    apply: bool = False,
    session: Session | None = None,
) -> OrganizeAPIResponse:
    """Extrae un frame central, clasifica con visión y opcionalmente mueve + indexa el clip."""
    path = video_path.resolve()
    if not path.is_file():
        raise FileNotFoundError(str(path))

    cfg = get_config()
    threshold = cfg.vision.classification_confidence_threshold
    library_root = cfg.resolved_paths()["library_root"]
    ffmpeg = FFmpegService()

    if cfg.runtime.local_only:
        classification = vision_service.classify_from_path_heuristic(path)
    else:
        tmp = Path(tempfile.gettempdir()) / f"aicos_organize_{uuid.uuid4().hex}.jpg"
        try:
            if not ffmpeg.is_available():
                raise RuntimeError("ffmpeg/ffprobe no disponibles en PATH")
            if not ffmpeg.extract_thumbnail(path, tmp, width=960, height=540, position=0.5):
                raise RuntimeError("No se pudo extraer frame para visión")

            llm = LLMService()
            classification = await vision_service.classify_frame(tmp, llm)
        finally:
            tmp.unlink(missing_ok=True)

    if not apply:
        return OrganizeAPIResponse(
            classification=classification,
            confidence_threshold=threshold,
            applied=False,
            destination_path=None,
            indexed=False,
            message="Modo simulación: no se movió el archivo.",
        )

    if session is None:
        raise ValueError("Se requiere sesión SQLAlchemy cuando apply=True")

    if classification.confidence < threshold:
        return OrganizeAPIResponse(
            classification=classification,
            confidence_threshold=threshold,
            applied=False,
            destination_path=None,
            indexed=False,
            message="Confianza por debajo del umbral; revisar manualmente (M4 needs_review).",
        )

    ctx_raw = (classification.context or "").strip()
    if ctx_raw.upper() in ("", "NULL", "NONE", "CONTEXT_OR_NULL"):
        ctx_raw = ""
    ctx_for_db = ctx_raw or None

    nxt = library_service.max_variant_number(
        session,
        classification.gender,
        classification.narrative_function,
        classification.subcategory,
        ctx_for_db,
        classification.is_ai_generated,
    )
    variant = nxt + 1
    fname = _build_filename(classification, variant)
    dest_dir = (library_root / _normalize_folder(classification.suggested_folder)).resolve()
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / fname

    shutil.move(str(path), str(dest))

    tax = parse_filename(dest.name)
    sem = build_semantic_text(tax, dest.name)
    meta_ff = ffmpeg.get_video_metadata(dest)
    file_hash = ffmpeg.compute_file_hash(dest)
    rel = str(dest.relative_to(library_root)).replace("\\", "/")

    thumbs = cfg.resolved_paths()["thumbnails_cache"]
    thumbs.mkdir(parents=True, exist_ok=True)
    thumb_path = thumbs / f"{file_hash}_thumb.jpg"
    thumb_ok = ffmpeg.extract_thumbnail(dest, thumb_path, width=cfg.ui.thumbnail_size[0], height=cfg.ui.thumbnail_size[1])

    clip_id = library_service.upsert_clip(
        session,
        clip_id=None,
        filename=dest.name,
        relative_path=rel,
        absolute_path=str(dest),
        gender=tax.gender,
        narrative_function=tax.narrative_function,
        subcategory=tax.subcategory,
        context=tax.context,
        variant_number=tax.variant_number,
        is_ai_generated=tax.is_ai_generated,
        semantic_text=sem,
        naming_compliant=tax.is_naming_compliant,
        needs_reclassification=not tax.is_naming_compliant,
        asset_kind=tax.asset_kind,
        file_hash=file_hash,
        duration_ms=meta_ff.duration_ms or None,
        resolution_width=meta_ff.width,
        resolution_height=meta_ff.height,
        file_size_bytes=meta_ff.file_size_bytes,
        thumbnail_path=str(thumb_path) if thumb_ok else None,
        embedding_id=None,
    )

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

    return OrganizeAPIResponse(
        classification=classification,
        confidence_threshold=threshold,
        applied=True,
        destination_path=str(dest),
        indexed=indexed,
        message=None,
    )
