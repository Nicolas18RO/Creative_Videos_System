"""Contrato de dominio de Clip Organization (M4). Sin I/O ni ORM."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

OrganizationAction = Literal["MOVE", "RENAME", "NONE"]
OrganizationRisk = Literal["NONE", "COLLISION", "INVALID", "UNSAFE", "INVALID_TAXONOMY"]
OrganizationMode = Literal["dry_run", "apply"]


@dataclass(frozen=True, slots=True)
class LibraryTaxonomy:
    """Cinco ejes de organización/naming de archivo. No es Clip Intelligence."""

    gender: str
    narrative_function: str
    subcategory: str
    context: str | None = None
    variant: int = 1
    is_ai_generated: bool = False


@dataclass(frozen=True, slots=True)
class OrganizationInput:
    """Entrada del organizador: clip físico + intención de colocación."""

    source_path: str
    library_root: str
    current_taxonomy: LibraryTaxonomy | None
    decision: OrganizationDecision
    apply: bool = False
    clip_id: str | None = None
    occupied_destinations: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class IncomingOrganizationSignal:
    """Señal portable de clasificación para M4.

    Puede originarse en filename, humano o un modelo futuro.
    M4 no interpreta provenance_model / provenance_version.
    """

    taxonomy: LibraryTaxonomy
    confidence: float | None = None
    source: str = "unknown"
    reason: str = ""
    provenance_model: str | None = None
    provenance_version: str | None = None


@dataclass(frozen=True, slots=True)
class OrganizationDecision:
    """Decisión de colocación en taxonomía de biblioteca (no contenido inferido)."""

    taxonomy: LibraryTaxonomy
    reason: str = ""
    confidence: float | None = None
    source: str = "unknown"


@dataclass(frozen=True, slots=True)
class OrganizationProposal:
    """Propuesta determinista de organización. No implica movimiento."""

    source_path: str
    destination_path: str
    proposed_filename: str
    proposed_relative_folder: str
    action: OrganizationAction
    risk: OrganizationRisk
    apply: bool
    eligible: bool
    reason: str
    confidence: float | None
    current_taxonomy: LibraryTaxonomy | None
    proposed_taxonomy: LibraryTaxonomy
    clip_id: str | None = None

    @property
    def mode(self) -> OrganizationMode:
        return "apply" if self.apply else "dry_run"


@dataclass(frozen=True, slots=True)
class OrganizationResult:
    """Resultado contractual. El dominio no ejecuta el filesystem."""

    applied: bool
    source_path: str
    destination_path: str | None
    risk: OrganizationRisk
    message: str
    proposal: OrganizationProposal
