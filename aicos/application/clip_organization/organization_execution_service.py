"""Ejecución segura de una propuesta de organización. Solo filesystem, sin DB."""

from __future__ import annotations

import logging
import shutil
from dataclasses import replace
from pathlib import Path

from aicos.application.clip_organization.organization_preview_service import preview_organization
from aicos.domain.clip_organization.entities import (
    LibraryTaxonomy,
    OrganizationDecision,
    OrganizationProposal,
    OrganizationResult,
    OrganizationRisk,
)
from aicos.domain.clip_organization.rules import is_safe_library_destination

logger = logging.getLogger(__name__)


def _result(
    proposal: OrganizationProposal,
    *,
    applied: bool,
    risk: OrganizationRisk,
    message: str,
    destination_path: str | None = None,
) -> OrganizationResult:
    marked = replace(proposal, apply=True, eligible=applied and risk == "NONE")
    dest = destination_path if destination_path is not None else (proposal.destination_path or None)
    return OrganizationResult(
        applied=applied,
        source_path=proposal.source_path,
        destination_path=dest,
        risk=risk,
        message=message,
        proposal=marked,
    )


def _revalidate_for_apply(
    *,
    source: Path,
    dest: Path,
    library_root: Path,
    proposal: OrganizationProposal,
) -> OrganizationResult | None:
    """Revalida source/destino. Devuelve un fallo o None si se puede ejecutar."""
    if proposal.risk != "NONE" or not proposal.eligible or not proposal.destination_path:
        return _result(
            proposal,
            applied=False,
            risk=proposal.risk if proposal.risk != "NONE" else "INVALID",
            message=f"Propuesta no elegible: {proposal.reason}",
        )
    if not source.is_file():
        return _result(
            proposal,
            applied=False,
            risk="INVALID",
            message="Archivo de origen no encontrado.",
        )
    if not is_safe_library_destination(str(library_root), str(dest)):
        return _result(
            proposal,
            applied=False,
            risk="UNSAFE",
            message="El destino propuesto escapa de library_root.",
        )
    if dest.exists() and dest.resolve() != source.resolve():
        return _result(
            proposal,
            applied=False,
            risk="COLLISION",
            message="El destino ya existe.",
        )
    return None


def execute_organization(
    *,
    source_path: Path,
    library_root: Path,
    decision: OrganizationDecision,
    current_taxonomy: LibraryTaxonomy | None = None,
    clip_id: str | None = None,
) -> OrganizationResult:
    """Ejecuta un move/rename validado. No sobrescribe. No reporta éxito falso.

    Args:
        source_path: Archivo físico a mover o renombrar.
        library_root: Raíz de la biblioteca.
        decision: Decisión de taxonomía de archivo.
        current_taxonomy: Taxonomía actual del filename, si se conoce.
        clip_id: Identidad de clip si ya existe.

    Returns:
        OrganizationResult. `applied=True` solo si el destino existe tras la operación.
    """
    preview = preview_organization(
        source_path=source_path,
        library_root=library_root,
        decision=decision,
        current_taxonomy=current_taxonomy,
        clip_id=clip_id,
    )
    proposal = replace(preview.proposal, apply=True)
    source = Path(proposal.source_path)
    dest = Path(proposal.destination_path) if proposal.destination_path else Path()
    root = Path(library_root)

    blocked = _revalidate_for_apply(source=source, dest=dest, library_root=root, proposal=proposal)
    if blocked is not None:
        return blocked

    if dest.resolve() == source.resolve():
        if not dest.is_file():
            return _result(
                proposal,
                applied=False,
                risk="INVALID",
                message="El destino coincide con el origen pero el archivo no existe.",
            )
        return _result(
            proposal,
            applied=True,
            risk="NONE",
            message="El archivo ya está en el destino propuesto.",
            destination_path=str(dest),
        )

    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(dest))
    except OSError as exc:
        logger.warning("Fallo al mover %s -> %s: %s", source, dest, exc)
        return _result(
            proposal,
            applied=False,
            risk="INVALID",
            message=f"No se pudo mover el archivo: {exc}",
            destination_path=str(dest),
        )

    if not dest.is_file():
        return _result(
            proposal,
            applied=False,
            risk="INVALID",
            message="El move no se pudo verificar: el destino no existe.",
            destination_path=str(dest),
        )

    return _result(
        proposal,
        applied=True,
        risk="NONE",
        message="Archivo organizado en el destino propuesto.",
        destination_path=str(dest.resolve()),
    )
