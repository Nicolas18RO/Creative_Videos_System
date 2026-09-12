"""Dry-run de organización: observa el filesystem y no lo modifica."""

from __future__ import annotations

from pathlib import Path

from aicos.domain.clip_organization.entities import (
    LibraryTaxonomy,
    OrganizationDecision,
    OrganizationInput,
    OrganizationProposal,
    OrganizationResult,
    OrganizationRisk,
)
from aicos.domain.clip_organization.rules import (
    build_organization_proposal,
    build_organized_filename,
    build_relative_folder,
    calculate_destination,
    is_valid_library_taxonomy,
    organization_result_from_proposal,
)
from aicos.models.schemas import TaxonomyResult


def library_taxonomy_from_parse(parsed: TaxonomyResult) -> LibraryTaxonomy | None:
    """Traduce un parse de filename a ejes de organización, si hay datos suficientes."""
    if not parsed.gender or not parsed.narrative_function or not parsed.subcategory:
        return None
    variant = parsed.variant_number if parsed.variant_number and parsed.variant_number >= 1 else 1
    return LibraryTaxonomy(
        gender=parsed.gender,
        narrative_function=parsed.narrative_function,
        subcategory=parsed.subcategory,
        context=parsed.context,
        variant=variant,
        is_ai_generated=parsed.is_ai_generated,
    )


def library_taxonomy_from_classification(
    gender: str,
    narrative_function: str,
    subcategory: str,
    context: str | None,
    *,
    variant: int = 1,
    is_ai_generated: bool = False,
) -> LibraryTaxonomy:
    """Construye ejes de organización desde una clasificación ya disponible."""
    return LibraryTaxonomy(
        gender=gender,
        narrative_function=narrative_function,
        subcategory=subcategory,
        context=context,
        variant=variant if variant >= 1 else 1,
        is_ai_generated=is_ai_generated,
    )


def _read_occupied_destination(library_root: Path, taxonomy: LibraryTaxonomy) -> tuple[str, ...]:
    dest = calculate_destination(str(library_root), taxonomy)
    if dest.exists():
        return (str(dest.resolve()),)
    return ()


def _proposal_without_write(
    *,
    source_path: str,
    library_root: str,
    decision: OrganizationDecision,
    current_taxonomy: LibraryTaxonomy | None,
    clip_id: str | None,
    risk: OrganizationRisk,
    reason: str,
) -> OrganizationProposal:
    filename = ""
    relative = ""
    dest = ""
    proposed = decision.taxonomy
    if is_valid_library_taxonomy(decision.taxonomy):
        filename = build_organized_filename(decision.taxonomy)
        relative = build_relative_folder(decision.taxonomy)
        dest = str(calculate_destination(library_root, decision.taxonomy))
    return OrganizationProposal(
        source_path=source_path,
        destination_path=dest,
        proposed_filename=filename,
        proposed_relative_folder=relative,
        action="NONE",
        risk=risk,
        apply=False,
        eligible=False,
        reason=reason,
        confidence=decision.confidence,
        current_taxonomy=current_taxonomy,
        proposed_taxonomy=proposed,
        clip_id=clip_id,
    )


def preview_organization(
    *,
    source_path: Path,
    library_root: Path,
    decision: OrganizationDecision,
    current_taxonomy: LibraryTaxonomy | None = None,
    clip_id: str | None = None,
) -> OrganizationResult:
    """Calcula la propuesta de organización sin mover, renombrar ni borrar.

    Args:
        source_path: Archivo de origen a organizar.
        library_root: Raíz de la biblioteca de destino.
        decision: Decisión de taxonomía de archivo (no Clip Intelligence).
        current_taxonomy: Taxonomía actual del filename, si se conoce.
        clip_id: Identidad de clip si ya existe en SQLite.

    Returns:
        OrganizationResult con `applied=False`. El filesystem no cambia.
    """
    source = Path(source_path)
    root = Path(library_root)

    if not str(root).strip() or root.is_file():
        proposal = _proposal_without_write(
            source_path=str(source),
            library_root=str(root),
            decision=decision,
            current_taxonomy=current_taxonomy,
            clip_id=clip_id,
            risk="INVALID",
            reason="Destino inválido: library_root no es un directorio.",
        )
        return organization_result_from_proposal(proposal)

    if not source.is_file():
        proposal = _proposal_without_write(
            source_path=str(source),
            library_root=str(root),
            decision=decision,
            current_taxonomy=current_taxonomy,
            clip_id=clip_id,
            risk="INVALID",
            reason="Archivo de origen no encontrado.",
        )
        return organization_result_from_proposal(proposal)

    occupied: tuple[str, ...] = ()
    if is_valid_library_taxonomy(decision.taxonomy):
        occupied = _read_occupied_destination(root, decision.taxonomy)

    inp = OrganizationInput(
        source_path=str(source.resolve()),
        library_root=str(root.resolve()),
        current_taxonomy=current_taxonomy,
        decision=decision,
        apply=False,
        clip_id=clip_id,
        occupied_destinations=occupied,
    )
    return organization_result_from_proposal(build_organization_proposal(inp))


class OrganizationPreviewService:
    """Puerto de aplicación para dry-run de M4."""

    def preview(
        self,
        *,
        source_path: Path,
        library_root: Path,
        decision: OrganizationDecision,
        current_taxonomy: LibraryTaxonomy | None = None,
        clip_id: str | None = None,
    ) -> OrganizationResult:
        return preview_organization(
            source_path=source_path,
            library_root=library_root,
            decision=decision,
            current_taxonomy=current_taxonomy,
            clip_id=clip_id,
        )
