"""Puerto de entrada de clasificación para M4.

Convierte una señal filename / humana / de modelo futuro en OrganizationDecision.
No interpreta provenance_model ni provenance_version.
"""

from __future__ import annotations

from aicos.application.clip_organization.organization_preview_service import (
    library_taxonomy_from_classification,
    library_taxonomy_from_parse,
)
from aicos.domain.clip_organization.entities import (
    IncomingOrganizationSignal,
    LibraryTaxonomy,
    OrganizationDecision,
)
from aicos.domain.clip_organization.rules import (
    build_organized_filename,
    build_relative_folder,
    is_valid_library_taxonomy,
    organization_decision_from_inbound,
)
from aicos.models.schemas import OrganizationDecisionBody, VisionClassification
from aicos.taxonomy.parser import parse_filename


def decision_from_inbound(signal: IncomingOrganizationSignal) -> OrganizationDecision:
    """Única conversión a decisión de organización. Descarta provenance de modelo."""
    return organization_decision_from_inbound(signal)


def incoming_signal_from_classification(
    classification: VisionClassification,
    *,
    source_name: str,
    source: str,
    reason: str = "clasificación M4 (filename/visión)",
) -> IncomingOrganizationSignal:
    """Adapta la clasificación actual (heurística o visión) al puerto inbound."""
    parsed = parse_filename(source_name)
    current = library_taxonomy_from_parse(parsed)
    variant = current.variant if current is not None else 1
    return IncomingOrganizationSignal(
        taxonomy=library_taxonomy_from_classification(
            classification.gender,
            classification.narrative_function,
            classification.subcategory,
            classification.context,
            variant=variant,
            is_ai_generated=classification.is_ai_generated,
        ),
        confidence=classification.confidence,
        source=source,
        reason=reason,
    )


def incoming_signal_from_body(body: OrganizationDecisionBody) -> IncomingOrganizationSignal:
    """Adapta una decisión HTTP (humana o de Intelligence futura) al puerto inbound."""
    return IncomingOrganizationSignal(
        taxonomy=library_taxonomy_from_classification(
            body.gender,
            body.narrative_function,
            body.subcategory,
            body.context,
            variant=body.variant,
            is_ai_generated=body.is_ai_generated,
        ),
        confidence=body.confidence,
        source=body.source,
        reason=body.reason,
        provenance_model=body.provenance_model,
        provenance_version=body.provenance_version,
    )


def current_taxonomy_from_source_name(source_name: str) -> LibraryTaxonomy | None:
    """Lee ejes actuales del filename. No es Clip Intelligence."""
    return library_taxonomy_from_parse(parse_filename(source_name))


def vision_classification_from_decision(decision: OrganizationDecision) -> VisionClassification:
    """Proyección de respuesta API. No vuelve a inferir contenido."""
    tax = decision.taxonomy
    filename = ""
    folder = ""
    if is_valid_library_taxonomy(tax):
        filename = build_organized_filename(tax)
        folder = f"{build_relative_folder(tax)}/"
    return VisionClassification(
        gender=tax.gender,
        narrative_function=tax.narrative_function,
        subcategory=tax.subcategory,
        context=tax.context,
        is_ai_generated=tax.is_ai_generated,
        suggested_filename=filename,
        suggested_folder=folder,
        confidence=float(decision.confidence or 0.0),
        tags=[decision.source],
    )
