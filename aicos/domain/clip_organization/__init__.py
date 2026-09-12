"""Dominio de Clip Organization (M4): contrato de organización física."""

from aicos.domain.clip_organization.entities import (
    IncomingOrganizationSignal,
    LibraryTaxonomy,
    OrganizationDecision,
    OrganizationInput,
    OrganizationProposal,
    OrganizationResult,
)
from aicos.domain.clip_organization.rules import (
    build_organization_proposal,
    build_organized_filename,
    build_relative_folder,
    calculate_destination,
    destination_collides,
    is_safe_library_destination,
    is_safe_source_path,
    is_valid_library_taxonomy,
    normalize_decision_source,
    organization_decision_from_inbound,
    organization_result_from_proposal,
)

__all__ = [
    "IncomingOrganizationSignal",
    "LibraryTaxonomy",
    "OrganizationDecision",
    "OrganizationInput",
    "OrganizationProposal",
    "OrganizationResult",
    "build_organization_proposal",
    "build_organized_filename",
    "build_relative_folder",
    "calculate_destination",
    "destination_collides",
    "is_safe_library_destination",
    "is_safe_source_path",
    "is_valid_library_taxonomy",
    "normalize_decision_source",
    "organization_decision_from_inbound",
    "organization_result_from_proposal",
]
