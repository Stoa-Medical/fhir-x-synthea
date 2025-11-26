"""Synthea PayerTransition → FHIR R4 Coverage"""

from typing import Any

from fhir.resources.coverage import Coverage
from synthea_pydantic import PayerTransition as SyntheaPayerTransition

from ..utils import to_str


def _map_relationship(ownership: str | None) -> dict[str, Any] | None:
    """Map ownership to FHIR relationship CodeableConcept."""
    if not ownership:
        return None
    ownership_lower = ownership.lower().strip()
    relationship_map = {
        "self": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/subscriber-relationship",
                    "code": "self",
                    "display": "Self",
                }
            ]
        },
        "spouse": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/subscriber-relationship",
                    "code": "spouse",
                    "display": "Spouse",
                }
            ]
        },
        "child": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/subscriber-relationship",
                    "code": "child",
                    "display": "Child",
                }
            ]
        },
        "guardian": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/subscriber-relationship",
                    "code": "parent",
                    "display": "Parent",
                }
            ]
        },
    }
    return relationship_map.get(ownership_lower)


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
    d = src.model_dump()

    # Extract fields
    patient_id = to_str(d.get("patient"))
    member_id = to_str(d.get("memberid"))
    start_year = d.get("start_year")
    end_year = d.get("end_year")
    payer_id = to_str(d.get("payer"))
    secondary_payer_id = to_str(d.get("secondary_payer"))
    ownership = to_str(d.get("ownership"))
    owner_name = to_str(d.get("owner_name"))

    # Determine status
    status = "active" if end_year is None else "cancelled"

    # Generate resource ID
    resource_id = f"{patient_id}-{payer_id}-{start_year}".replace(" ", "-")

    # Build resource
    resource: dict[str, Any] = {
        "resourceType": "Coverage",
        "status": status,
        "kind": "insurance",
    }

    if resource_id:
        resource["id"] = resource_id

    # Set beneficiary
    effective_patient_ref = patient_ref or (
        f"Patient/{patient_id}" if patient_id else None
    )
    if effective_patient_ref:
        resource["beneficiary"] = {"reference": effective_patient_ref}

    # Set subscriber (same as beneficiary for self)
    if effective_patient_ref:
        resource["subscriber"] = {"reference": effective_patient_ref}

    # Set subscriberId
    if member_id:
        resource["subscriberId"] = member_id

    # Set relationship
    relationship = _map_relationship(ownership)
    if relationship:
        resource["relationship"] = relationship

    # Set period
    if start_year is not None or end_year is not None:
        period: dict[str, Any] = {}
        if start_year is not None:
            period["start"] = f"{start_year}-01-01"
        if end_year is not None:
            period["end"] = f"{end_year}-12-31"
        if period:
            resource["period"] = period

    # Set insurer (payer)
    if payer_id:
        resource["insurer"] = {"reference": f"Organization/{payer_id}"}

    # Set extensions for secondary payer and owner
    extensions = []
    if secondary_payer_id:
        extensions.append(
            {
                "url": "http://synthea.mitre.org/fhir/StructureDefinition/secondary-payer",
                "valueReference": {"reference": f"Organization/{secondary_payer_id}"},
            }
        )
    if owner_name:
        extensions.append(
            {
                "url": "http://synthea.mitre.org/fhir/StructureDefinition/owner-name",
                "valueString": owner_name,
            }
        )

    if extensions:
        resource["extension"] = extensions

    return Coverage(**resource)
