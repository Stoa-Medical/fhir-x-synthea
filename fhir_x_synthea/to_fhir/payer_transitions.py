"""Synthea PayerTransition → FHIR R4 Coverage"""

from fhir.resources.coverage import Coverage
from synthea_pydantic import PayerTransition as SyntheaPayerTransition

from ..chidian_ext import grab, mapper, to_dict


def _resource_id(d: dict) -> str:
    """Generate deterministic resource ID."""
    patient_id = grab(d, "patient") or ""
    payer_id = grab(d, "payer") or ""
    start_year = grab(d, "start_year") or ""
    return f"{patient_id}-{payer_id}-{start_year}".replace(" ", "-")


def _map_relationship(ownership: str | None):
    """Map ownership to FHIR relationship CodeableConcept."""
    if not ownership:
        return None
    mapping = {
        "self": ("self", "Self"),
        "spouse": ("spouse", "Spouse"),
        "child": ("child", "Child"),
        "guardian": ("parent", "Parent"),
    }
    entry = mapping.get(ownership.lower().strip())
    if not entry:
        return None
    code, display = entry
    return {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/subscriber-relationship",
                "code": code,
                "display": display,
            }
        ]
    }


def _coverage_period(start_year, end_year):
    """Build coverage period."""
    if start_year is None and end_year is None:
        return None
    result = {}
    if start_year is not None:
        result["start"] = f"{start_year}-01-01"
    if end_year is not None:
        result["end"] = f"{end_year}-12-31"
    return result if result else None


def _secondary_payer_extension(secondary_payer_id: str | None):
    """Build secondary payer extension."""
    if not secondary_payer_id:
        return None
    return {
        "url": "http://synthea.mitre.org/fhir/StructureDefinition/secondary-payer",
        "valueReference": {"reference": f"Organization/{secondary_payer_id}"},
    }


def _owner_name_extension(owner_name: str | None):
    """Build owner name extension."""
    if not owner_name:
        return None
    return {
        "url": "http://synthea.mitre.org/fhir/StructureDefinition/owner-name",
        "valueString": owner_name,
    }


@mapper
def _to_fhir_coverage(d: dict, patient_ref: str | None = None):
    """Core mapping from dict to FHIR Coverage structure."""
    patient_id = grab(d, "patient")
    end_year = grab(d, "end_year")

    effective_patient_ref = patient_ref or (
        f"Patient/{patient_id}" if patient_id else None
    )

    # Build extensions list
    extensions = [
        e
        for e in [
            _secondary_payer_extension(grab(d, "secondary_payer")),
            _owner_name_extension(grab(d, "owner_name")),
        ]
        if e
    ]

    payer_id = grab(d, "payer")

    return {
        "resourceType": "Coverage",
        "id": _resource_id(d),
        "status": "cancelled" if end_year is not None else "active",
        "kind": "insurance",
        "beneficiary": {"reference": effective_patient_ref}
        if effective_patient_ref
        else None,
        "subscriber": {"reference": effective_patient_ref}
        if effective_patient_ref
        else None,
        "subscriberId": grab(d, "memberid"),
        "relationship": _map_relationship(grab(d, "ownership")),
        "period": _coverage_period(grab(d, "start_year"), end_year),
        "insurer": {"reference": f"Organization/{payer_id}"} if payer_id else None,
        "extension": extensions if extensions else None,
    }


def convert(
    src: SyntheaPayerTransition,
    *,
    patient_ref: str | None = None,
) -> Coverage:
    """Convert Synthea PayerTransition to FHIR R4 Coverage.

    Args:
        src: Synthea PayerTransition model
        patient_ref: Optional patient reference (e.g., "Patient/123")

    Returns:
        FHIR R4 Coverage resource
    """
    return Coverage(**_to_fhir_coverage(to_dict(src), patient_ref))
