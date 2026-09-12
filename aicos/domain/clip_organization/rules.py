"""Reglas puras de Clip Organization. Sin filesystem, DB ni modelos de IA."""

from __future__ import annotations

import re
from pathlib import Path, PurePosixPath, PureWindowsPath

from aicos.domain.clip_organization.entities import (
    IncomingOrganizationSignal,
    LibraryTaxonomy,
    OrganizationAction,
    OrganizationDecision,
    OrganizationInput,
    OrganizationProposal,
    OrganizationResult,
)
from aicos.taxonomy.constants import LEGACY_GENDER_PREFIXES, NARRATIVE_FUNCTIONS

_CANONICAL_GENDERS = frozenset({"F", "M", "N", "MIX", "KIDS"})
_NULL_CONTEXT = frozenset({"", "NULL", "NONE", "CONTEXT_OR_NULL"})
_TOKEN_RE = re.compile(r"^[A-Z0-9]+(?:_[A-Z0-9]+)*$")
_FILENAME_SOURCES = frozenset({"filename", "vision", "filename_heuristic", "local_filename"})
_HUMAN_SOURCES = frozenset({"human", "review", "manual"})
_MODEL_SOURCES = frozenset({"model", "intelligence", "clip_intelligence"})


def normalize_decision_source(raw: str | None) -> str:
    """Normaliza la procedencia a filename | human | model | unknown. Sin nombres de modelo."""
    token = (raw or "unknown").strip().lower()
    if token in _FILENAME_SOURCES:
        return "filename"
    if token in _HUMAN_SOURCES:
        return "human"
    if token in _MODEL_SOURCES:
        return "model"
    if token in {"filename", "human", "model", "unknown"}:
        return token
    if token:
        return "model"
    return "unknown"


def organization_decision_from_inbound(signal: IncomingOrganizationSignal) -> OrganizationDecision:
    """Convierte una señal externa en decisión de M4. Descarta provenance de modelo."""
    return OrganizationDecision(
        taxonomy=signal.taxonomy,
        reason=signal.reason,
        confidence=signal.confidence,
        source=normalize_decision_source(signal.source),
    )


def _normalize_token(raw: str) -> str:
    return raw.strip().upper().replace(" ", "_")


def _normalize_context(raw: str | None) -> str | None:
    if raw is None:
        return None
    token = _normalize_token(raw)
    if token in _NULL_CONTEXT:
        return None
    return token


def normalize_gender(raw: str) -> str | None:
    """Normaliza un prefijo de género a los cinco valores canónicos."""
    token = _normalize_token(raw)
    token = LEGACY_GENDER_PREFIXES.get(token, token)
    if token in _CANONICAL_GENDERS:
        return token
    return None


def is_valid_library_taxonomy(taxonomy: LibraryTaxonomy) -> bool:
    """Valida los cinco ejes de naming/carpeta. No valida semántica de contenido."""
    gender = normalize_gender(taxonomy.gender)
    function = _normalize_token(taxonomy.narrative_function)
    subcategory = _normalize_token(taxonomy.subcategory)
    context = _normalize_context(taxonomy.context)
    if gender is None:
        return False
    if function not in NARRATIVE_FUNCTIONS:
        return False
    if not subcategory or not _TOKEN_RE.fullmatch(subcategory):
        return False
    if context is not None and not _TOKEN_RE.fullmatch(context):
        return False
    if taxonomy.variant < 1:
        return False
    return True


def canonicalize_taxonomy(taxonomy: LibraryTaxonomy) -> LibraryTaxonomy:
    """Devuelve ejes normalizados. Requiere taxonomía válida."""
    gender = normalize_gender(taxonomy.gender)
    if gender is None:
        raise ValueError("invalid gender")
    return LibraryTaxonomy(
        gender=gender,
        narrative_function=_normalize_token(taxonomy.narrative_function),
        subcategory=_normalize_token(taxonomy.subcategory),
        context=_normalize_context(taxonomy.context),
        variant=int(taxonomy.variant),
        is_ai_generated=bool(taxonomy.is_ai_generated),
    )


def build_organized_filename(taxonomy: LibraryTaxonomy) -> str:
    """Construye el filename canónico de biblioteca (misma convención que M4)."""
    tax = canonicalize_taxonomy(taxonomy)
    parts = [tax.gender, tax.narrative_function, tax.subcategory]
    if tax.context:
        parts.append(tax.context)
    if tax.is_ai_generated:
        parts.append("IA")
    parts.append(f"{tax.variant:02d}")
    return "_".join(parts) + ".mp4"


def build_relative_folder(taxonomy: LibraryTaxonomy) -> str:
    """Carpeta relativa POSIX bajo library_root: GENDER/FUNCTION/SUBCATEGORY[/CONTEXT]."""
    tax = canonicalize_taxonomy(taxonomy)
    parts = [tax.gender, tax.narrative_function, tax.subcategory]
    if tax.context:
        parts.append(tax.context)
    return "/".join(parts)


def _as_path(raw: str) -> Path:
    return Path(raw)


def _normalized_key(raw: str) -> str:
    return str(_as_path(raw)).replace("\\", "/").casefold()


def is_safe_library_destination(library_root: str, destination: str) -> bool:
    """True si `destination` queda estrictamente dentro de `library_root`."""
    if not library_root or not destination:
        return False
    root = _as_path(library_root)
    dest = _as_path(destination)
    if dest.is_absolute() and not _is_relative_to(dest, root):
        return False
    if not dest.is_absolute():
        dest = root / dest
    for part in dest.parts:
        if part in {".", ".."}:
            return False
    return _is_relative_to(dest, root)


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except (OSError, ValueError):
        return False


def is_safe_source_path(source_path: str) -> bool:
    """Rechaza source vacío, relativo con `..` o con tokens inseguros."""
    if not source_path or not source_path.strip():
        return False
    raw = source_path.strip()
    posix = PurePosixPath(raw.replace("\\", "/"))
    win = PureWindowsPath(raw)
    if ".." in posix.parts or ".." in win.parts:
        return False
    return True


def calculate_destination(library_root: str, taxonomy: LibraryTaxonomy) -> Path:
    """Destino absoluto determinista a partir de library_root + taxonomía."""
    rel = build_relative_folder(taxonomy)
    name = build_organized_filename(taxonomy)
    return (_as_path(library_root) / Path(rel) / name)


def destination_collides(
    destination: str,
    *,
    source_path: str,
    occupied_destinations: tuple[str, ...],
) -> bool:
    """Colisión si el destino ya está ocupado por una ruta distinta al source."""
    dest_key = _normalized_key(destination)
    source_key = _normalized_key(source_path)
    if dest_key == source_key:
        return False
    occupied = {_normalized_key(p) for p in occupied_destinations}
    return dest_key in occupied


def _infer_action(source_path: str, destination: str) -> OrganizationAction:
    src = _as_path(source_path)
    dest = _as_path(destination)
    if _normalized_key(source_path) == _normalized_key(destination):
        return "NONE"
    if src.name != dest.name and src.parent == dest.parent:
        return "RENAME"
    return "MOVE"


def _risk_for_input(inp: OrganizationInput) -> tuple[OrganizationRisk, str]:
    if not is_safe_source_path(inp.source_path) or not (inp.library_root or "").strip():
        return "UNSAFE", "Ruta de origen o library_root inválida."
    if not is_valid_library_taxonomy(inp.decision.taxonomy):
        return "INVALID_TAXONOMY", "Taxonomía de organización inválida."
    dest = calculate_destination(inp.library_root, inp.decision.taxonomy)
    if not is_safe_library_destination(inp.library_root, str(dest)):
        return "UNSAFE", "El destino propuesto escapa de library_root."
    if destination_collides(
        str(dest),
        source_path=inp.source_path,
        occupied_destinations=inp.occupied_destinations,
    ):
        return "COLLISION", "El destino ya existe."
    return "NONE", inp.decision.reason or "Propuesta de organización de biblioteca."


def build_organization_proposal(inp: OrganizationInput) -> OrganizationProposal:
    """Calcula una propuesta determinista. Nunca mueve archivos."""
    risk, reason = _risk_for_input(inp)
    eligible = risk == "NONE"
    filename = ""
    relative = ""
    dest = ""
    action: OrganizationAction = "NONE"
    proposed = inp.decision.taxonomy
    if risk != "INVALID_TAXONOMY":
        try:
            proposed = canonicalize_taxonomy(inp.decision.taxonomy)
            filename = build_organized_filename(proposed)
            relative = build_relative_folder(proposed)
            dest = str(calculate_destination(inp.library_root, proposed))
            action = _infer_action(inp.source_path, dest) if eligible else "NONE"
        except ValueError:
            risk = "INVALID_TAXONOMY"
            reason = "Taxonomía de organización inválida."
            eligible = False
            dest = ""
            filename = ""
            relative = ""
            action = "NONE"
    if risk == "UNSAFE":
        dest = dest or ""
        action = "NONE"
        eligible = False
    return OrganizationProposal(
        source_path=inp.source_path,
        destination_path=dest,
        proposed_filename=filename,
        proposed_relative_folder=relative,
        action=action,
        risk=risk,
        apply=inp.apply,
        eligible=eligible,
        reason=reason,
        confidence=inp.decision.confidence,
        current_taxonomy=inp.current_taxonomy,
        proposed_taxonomy=proposed,
        clip_id=inp.clip_id,
    )


def organization_result_from_proposal(proposal: OrganizationProposal) -> OrganizationResult:
    """Materializa el resultado contractual. El dominio nunca aplica el move."""
    if proposal.apply and proposal.eligible:
        message = "Apply solicitado; la ejecución de filesystem no pertenece al contrato de dominio."
    elif proposal.apply and not proposal.eligible:
        message = f"Apply rechazado: {proposal.reason}"
    elif proposal.reason:
        message = f"Dry-run: no se movió el archivo. {proposal.reason}"
    else:
        message = "Dry-run: no se movió el archivo."
    return OrganizationResult(
        applied=False,
        source_path=proposal.source_path,
        destination_path=proposal.destination_path or None,
        risk=proposal.risk,
        message=message,
        proposal=proposal,
    )
